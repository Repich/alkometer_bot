# bot/handlers/start.py

from bot.logger import logger
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes
from bot.utils.db import SessionLocal
from bot.models.user import User
from bot.utils.keyboards import main_menu_keyboard


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Выполняется обработчик /start")
    session = SessionLocal()
    user_id = update.effective_user.id
    username = update.effective_user.username

    # Проверяем, существует ли пользователь
    user = session.query(User).filter(User.telegram_id == user_id).first()

    if not user:
        # Создаем нового пользователя
        user = User(telegram_id=user_id, username=username)
        session.add(user)
        session.commit()
        welcome_text = "Добро пожаловать в Alkometer! Теперь вы можете отслеживать потребление алкоголя."
    else:
        # Если пользователь уже есть, не отправляем сообщение "С возвращением", а сразу переходим к меню
        welcome_text = None  # Нет необходимости отправлять это сообщение

    # Создание главного меню
    reply_keyboard = [['Добавить алкоголь', 'Просмотр отчёта'], ['Настройки']]
    await update.message.reply_text(
        welcome_text if welcome_text else "Как я могу помочь?",
        reply_markup=main_menu_keyboard(),
    )
    session.close()


# Регистрация обработчика команды /start
start_handler = CommandHandler('start', start)
