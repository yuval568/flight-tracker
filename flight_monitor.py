import os
import requests

API_KEY = os.environ["SERPAPI_KEY"]

TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_CONTENT_SID = os.environ["TWILIO_CONTENT_SID"]
TWILIO_WHATSAPP = os.environ["TWILIO_WHATSAPP"]
MY_WHATSAPP = os.environ["MY_WHATSAPP"]

date_options = [
    ("2027-04-14", "2027-05-05"),
    ("2027-04-14", "2027-05-06"),
    ("2027-04-15", "2027-05-05"),
    ("2027-04-15", "2027-05-06"),
]

BASE_URL = "https://serpapi.com/search.json"
MAX_DURATION = 900  # 15 hours


api_calls = 0

def search(params):
    global api_calls
    api_calls += 1

    params["api_key"] = API_KEY

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=60
    )

    response.raise_for_status()
    return response.json()


def base_params(outbound_date, return_date):
    return {
        "engine": "google_flights",
        "departure_id": "TLV",
        "arrival_id": "BKK",
        "outbound_date": outbound_date,
        "return_date": return_date,
        "currency": "USD",
        "hl": "en",
        "gl": "il",
        "type": "1",
    }



def get_single_airline(flight):
    """Return the airline only if every segment in this direction uses the same airline."""
    airlines = {
        segment.get("airline")
        for segment in flight.get("flights", [])
        if segment.get("airline")
    }
    return next(iter(airlines)) if len(airlines) == 1 else None

def get_market_status(outbound_date, return_date):
    # No duration filter here, because we want Google's price insights
    data = search(base_params(outbound_date, return_date))

    return data.get("price_insights")

def get_airlines(flight_option):
    """Return unique airline names for all segments in one flight option."""
    airlines = []
    for segment in flight_option.get("flights", []):
        airline = segment.get("airline")
        if airline and airline not in airlines:
            airlines.append(airline)
    return airlines


def format_airlines(outbound_airlines, return_airlines):
    """Combine outbound/return airlines without duplicates, preserving order."""
    airlines = []
    for airline in outbound_airlines + return_airlines:
        if airline and airline not in airlines:
            airlines.append(airline)
    return " / ".join(airlines) if airlines else "Unknown"


def get_best_round_trip(outbound_date, return_date):
    params = base_params(outbound_date, return_date)
    params["max_duration"] = MAX_DURATION

    outbound_data = search(params)

    outbound_flights = (
        outbound_data.get("best_flights", [])
        + outbound_data.get("other_flights", [])
    )

    # Safety check + sort by displayed price
    outbound_flights = [
        flight for flight in outbound_flights
        if flight.get("total_duration", 999999) <= MAX_DURATION
        and flight.get("departure_token")
        and flight.get("price") is not None
        and get_single_airline(flight) is not None
    ]

    outbound_flights.sort(key=lambda flight: flight["price"])

    best_trip = None

    for outbound in outbound_flights:

        # If we already found a round trip cheaper than the starting
        # price of this option, there's no reason to continue.
        if best_trip and outbound["price"] >= best_trip["price"]:
            break

        return_params = base_params(outbound_date, return_date)
        return_params["max_duration"] = MAX_DURATION
        return_params["departure_token"] = outbound["departure_token"]

        return_data = search(return_params)

        return_flights = (
            return_data.get("best_flights", [])
            + return_data.get("other_flights", [])
        )

        valid_returns = [
            flight for flight in return_flights
            if flight.get("total_duration", 999999) <= MAX_DURATION
            and flight.get("price") is not None
            and get_single_airline(flight) is not None
        ]

        if not valid_returns:
            continue

        cheapest_return = min(
            valid_returns,
            key=lambda flight: flight["price"]
        )

        outbound_airlines = get_airlines(outbound)
        return_airlines = get_airlines(cheapest_return)

        candidate = {
            "price": cheapest_return["price"],
            "outbound_duration": outbound["total_duration"],
            "return_duration": cheapest_return["total_duration"],
            "outbound_date": outbound_date,
            "return_date": return_date,
            "outbound_airline": get_single_airline(outbound),
            "return_airline": get_single_airline(cheapest_return),
            "airlines": format_airlines(outbound_airlines, return_airlines),
        }

        if best_trip is None or candidate["price"] < best_trip["price"]:
            best_trip = candidate

    return best_trip


def send_whatsapp_test():
    """Send Twilio's Trial template to prove the monitor reached the notification step."""
    url = (
        f"https://api.twilio.com/2010-04-01/"
        f"Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    )

    data = {
        "To": MY_WHATSAPP,
        "From": TWILIO_WHATSAPP,
        "ContentSid": TWILIO_CONTENT_SID,
    }

    response = requests.post(
        url,
        data=data,
        auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
        timeout=30,
    )

    if response.status_code == 201:
        print("📲 WhatsApp notification queued successfully.")
        return True

    print("❌ WhatsApp notification failed:")
    print(response.status_code)
    print(response.text)
    return False


all_valid_trips = []
market_data = {}


for outbound_date, return_date in date_options:

    print(f"Checking {outbound_date} -> {return_date}...")

    # 1. Google's general market status
    insights = get_market_status(outbound_date, return_date)

    if insights:
        market_data[(outbound_date, return_date)] = insights

    # 2. Actual flights where BOTH directions <= 15h
    trip = get_best_round_trip(outbound_date, return_date)

    if trip:
        all_valid_trips.append(trip)


if all_valid_trips:

    best = min(
        all_valid_trips,
        key=lambda trip: trip["price"]
    )

    insights = market_data.get(
        (best["outbound_date"], best["return_date"])
    )

    print("\n✈️ Thailand Flight Update 🌴")
    print(
        f"📅 {best['outbound_date']} → "
        f"{best['return_date']}"
    )
    print(f"💰 Price: ${best['price']}")
    print(f"🛫 Outbound airline: {best['outbound_airline']}")
    print(f"🛬 Return airline: {best['return_airline']}")

    if insights:

        level = insights.get("price_level", "unknown")
        
        print(f"📊 Market status: {level}")

    # Trial limitation: this currently sends Twilio's built-in test template.
    # Once the account is upgraded, we can replace it with a custom template
    # containing the date, price and market status printed above.
    send_whatsapp_test()

else:
    print("\n😕 No suitable flights found.")
    
print(f"\n🔎 API calls used: {api_calls}")
