import asyncio
import logging
import os
import json
import sys
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# 1. Загружаем переменные окружения
load_dotenv()

# Получаем токены и URL из .env файла
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL")
ADMIN_ID_STR = os.getenv("ADMIN_ID")
ADMIN_ID = int(ADMIN_ID_STR) if ADMIN_ID_STR and ADMIN_ID_STR.isdigit() else None

# Инициализация роутера
router = Dispatcher(storage=MemoryStorage())

# ================ ХЭНДЛЕРЫ КОМАНД ================

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """
    Обработчик команды /start.
    Отправляет приветственное сообщение и кнопку для запуска Web App.
    """
    logging.info(f"User {message.from_user.id} started the bot.")
    
    # Создаем кнопку, которая открывает Web App
    web_app_button = types.KeyboardButton(
        text="🏠 Собрать проект дома", 
        web_app=types.WebAppInfo(url=WEB_APP_URL)
    )
    
    # Собираем клавиатуру
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[web_app_button]], 
        resize_keyboard=True
    )
    
    await message.answer(
        "Привет! Я ИИ-архитектор. 🤖\n\n"
        "Нажми кнопку ниже, чтобы запустить конструктор и создать проект дома своей мечты!", 
        reply_markup=keyboard
    )

@router.message(Command("stop"))
async def cmd_stop(message: types.Message, dp: Dispatcher):
    """
    Обработчик команды /stop для администратора.
    Выполняет корректную остановку бота.
    """
    if not ADMIN_ID or message.from_user.id != ADMIN_ID:
        logging.warning(f"Unauthorized stop attempt by user {message.from_user.id}")
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return

    logging.info(f"Stop command received from admin {ADMIN_ID}. Shutting down...")
    await message.answer("✅ Бот останавливается... Процесс может занять несколько секунд.")
    
    # Корректно останавливаем поллинг
    await dp.stop_polling()

# ================ ХЭНДЛЕР ДЛЯ WEB APP ================

@router.message(F.web_app_data)
async def answer_web_app(message: types.Message):
    """
    Ловит данные, отправленные из Web App.
    """
    try:
        user_id = message.from_user.id
        # Получаем данные в виде строки
        json_string = message.web_app_data.data
        
        logging.info(f"Received Web App data from user {user_id}: {json_string}")
        
        # Превращаем строку в Python-словарь (JSON)
        data = json.loads(json_string)
        
        # Извлекаем выбранный стиль, используем .get() для безопасности
        style = data.get('style', 'не выбран')
        
        await message.answer(
            f"Отлично! Ваш выбор принят.\n\n"
            f"🎨 <b>Выбранный стиль:</b> <code>{style.capitalize()}</code>\n\n"
            "Сейчас я бы начал генерировать планировки и смету, но этот функционал еще в разработке. 🛠️"
        )

        # Здесь в будущем будет вызов функций для генерации картинок и сметы
        # Например:
        # await generate_layouts(style)
        # await calculate_estimate(style)

    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON from Web App: {message.web_app_data.data}")
        await message.answer("Произошла ошибка при обработке данных. Попробуйте еще раз. 😵‍💫")
    except Exception as e:
        logging.error(f"An unexpected error occurred in answer_web_app: {e}", exc_info=True)
        await message.answer("Что-то пошло не так на сервере. Мы уже разбираемся! 🛠️")


# ================ ФУНКЦИЯ ЗАПУСКА ================

async def main():
    """Главная функция для запуска бота"""

    # Проверка наличия обязательных переменных
    if not BOT_TOKEN or not WEB_APP_URL:
        error_msg = "ОШИБКА: Отсутствуют переменные окружения в файле .env. Проверьте BOT_TOKEN и WEB_APP_URL."
        logging.critical(error_msg)
        print("="*60, f"\n{error_msg}\n", "="*60)
        return

    # Настраиваем объект бота
    default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=default_properties)
    
    # Удаляем старые вебхуки и запускаем поллинг
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("="*60)
    print("🤖 Бот-архитектор запущен!")
    print("="*60)

    try:
        # Передаем объект dp в start_polling, чтобы он был доступен в хендлере /stop
        await router.start_polling(bot, dp=router)
    finally:
        # Этот блок выполнится при любой остановке (Ctrl+C или /stop)
        await bot.session.close()
        logging.warning("Бот остановлен и ресурсы очищены.")

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"
    )
    
    # Для корректной работы в Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Получен сигнал на остановку (Ctrl+C). Завершение работы...")