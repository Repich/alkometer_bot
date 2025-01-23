# bot/config.py

import os
from bot.logger import logger
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

logger.info(f"TELEGRAM_BOT_TOKEN загружен: {'Да' if TELEGRAM_BOT_TOKEN else 'Нет'}")

