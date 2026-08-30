# ✈️ Thailand Flight Monitor

> **Python · SerpApi · Google Flights · GitHub Actions · Twilio ·
> WhatsApp**

I took responsibility for booking our family trip to Thailand for
Passover --- five people in total.

Then I discovered two things: flights were already painfully expensive,
and had I booked a month earlier, they would have been much cheaper.
Even worse, flight prices don't move in a straight line --- a good deal
could randomly show up tomorrow.

So naturally, I started checking **Google Flights** and **Skyscanner**
almost every day.

That got old pretty quickly.

## 💡 There had to be a better way

I found **SerpApi**, which lets me retrieve Google Flights data in a
structured format, and wrote a **Python** script to do the searching for
me.

It checks a few flexible departure/return dates and filters for: - no
more than one stop - up to 15 hours per direction *(not everyone in the
family is young and enthusiastic 😅)* - the same airline across each
direction - the cheapest option that fits

Then I used **GitHub Actions** to run it automatically in the cloud
every few days --- no laptop, no daily refreshing.

## 📱 One piece was still missing

I wanted the family involved in the process.

And yes, I also wanted to show off a little.

So with some help from **ChatGPT**, I connected **Twilio** to send the
latest result through WhatsApp: dates, price, airline and Google Flights
market status.

### ⚙️ The result

**Google Flights → SerpApi → Python → GitHub Actions → Twilio → WhatsApp
📱**

A small system that checks the flights every few days and sends the
result automatically.

Now I just need the prices to cooperate. 🤞

### 🧰 Built with

**Python** · **SerpApi** · **Google Flights** · **GitHub Actions** ·
**Twilio** · **WhatsApp**
