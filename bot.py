import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "7727645806:AAG7M5WxZ3aKrEil7onoaBBYPdXrE54YfaA"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! 🌤 Ob-havo bot ishlayapti.\n/weather buyrug'ini yozing.")

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": 41.2995,
        "longitude": 69.2401,
        "current_weather": True
    }

    r = requests.get(url, params=params).json()

    temp = r["current_weather"]["temperature"]
    wind = r["current_weather"]["windspeed"]

    text = f"🌤 Toshkent ob-havo\n\n🌡 Harorat: {temp}°C\n💨 Shamol: {wind} m/s"

    await update.message.reply_text(text)


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("weather", weather))

app.run_polling()
