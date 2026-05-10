'''Системные импорты'''
import asyncio
import logging
from datetime import datetime
import os
from dotenv import load_dotenv

'''Импорты из aiogram'а'''
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler

'''Импорт БД'''
from database import Database

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("OPENWEATHER_API_KEY")

db = Database(os.getenv("DATABASE_URL"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

scheduler = AsyncIOScheduler()

Message = types.Message

'''Получение информации о погоде'''
async def get_weather(city: str):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    async with ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            if data["cod"] == 200: # Проверка правильности запроса по коду в JSON
                '''Парсинг и ответ'''
                temperature = data['main']['temp']
                description = data['weather'][0]['description']
                feel = data['main']['feels_like']
                rucity = data['name']
                return f'В городе {rucity} сейчас {temperature}°C, ощущается как {feel}, {description}.'
            return False
        
'''Отправка отчёта всем пользователям'''
async def send_hourly_weather():
    users = await db.get_all_users() # Получение списка всех пользователей
    for user in users:
        weather_text = await get_weather(user.city)
        if weather_text:
            try:
                await bot.send_message(user.userID, f"Ежечасный отчёт о погоде:\n{weather_text}")
            except Exception:
                logging.error(f'Ошибка при отправке {user.userID}: {Exception}')

'''Обработчик команды /start'''
@dp.message(Command("start"))
async def start(message: Message):
    await db.add_user(message.from_user.id) # Добавление нового пользователя в БД
    user = await db.get_user(message.from_user.id)
    await message.answer(f"Теперь тебе каждый час будет приходить отчёт о погоде.\nСейчас у тебя выбран город {user.city}. Чтобы изменить город, напиши: /setcity City_name.\nЧтобы проверить погоду сейчас, напиши /now")


'''Обработчик команды /setcity args'''
@dp.message(Command("setcity"))
async def setcity(message: Message):
    args = message.text.split(maxsplit=1) # Разбивка команды на слова
    if len(args) < 2: # Случай, когда команда без аргументов
        return await message.answer("Город не указан или указан неверно. Пример, корректного запроса: '/setcity Токио'")
    new_city = args[1].strip() # Получение чистого названия города
    weather_check = await get_weather(new_city) # Запрос о погоде в этом городе
    if weather_check: # Проверка на существование города
        await db.update_city(message.from_user.id, new_city) # Перезапись данных в БД
        await message.answer(f"Город изменён на {new_city}.\{weather_check}", parse_mode="Markdown")
    else:
        await message.answer("Не нашёл такого города. Проверь название")

'''Обработчик команды /now'''
@dp.message(Command("now"))
async def now(message: Message):
    user = await db.get_user(message.from_user.id)
    weather = await get_weather(user.city)
    if weather:
        await message.answer(f"{weather}") 
    else:
        await message.answer("Не удалось получить данные")

'''Главная функция'''
async def main():
    logging.basicConfig(level=logging.INFO)
    await db.create_tables() # Создание таблиц в БД
    scheduler.add_job(send_hourly_weather, "interval", hours=1) # Создание цикла, который в xx:00 отправляет всем отчёт о погоде
    scheduler.start() # Старт цикла
    await dp.start_polling(bot) # Старт бота

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот выключен')