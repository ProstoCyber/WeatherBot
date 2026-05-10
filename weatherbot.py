import asyncio
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITY = os.getenv("CITY")

bot = Bot(token=TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
Message = types.Message

users_IDs = set()

async def get_weather():
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={API_KEY}&units=metric&lang=ru"
    async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                temperature = data['main']['temp']
                description = data['weather'][0]['description']
                return f'В городе {CITY} сейчас {temperature} градусов по Цельсию. {description}'
            return "Не удалось получить данные"
        
async def send_hourly_weather():
    if not users_IDs:
        return
    weather_text = await get_weather()
    for userID in users_IDs:
        try:
            await bot.send_message(userID, f"Ежечасный отчёт о погоде:\n\n{weather_text}")
        except Exception:
            logging.error(f'Ошибка при отправке {userID}: {Exception}')

@dp.message(Command("start"))
async def start(message: Message):
    if message.chat.id not in users_IDs:
        users_IDs.add(message.chat.id)
    await message.answer(f"Теперь тебе каждый час будет приходить отчёт о погоде в городе {CITY}.\nВот последний отчёт:\n{await get_weather()}")

async def main():
    logging.basicConfig(level=logging.INFO)
    scheduler.add_job(send_hourly_weather, "interval", hours=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')