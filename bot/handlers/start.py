# bot/handlers/start.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.db import SessionLocal
from bot.models.user import User
from bot.logger import logger

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Выполняется обработчик /start")
    session = SessionLocal()
    user_id = update.effective_user.id
    username = update.effective_user.username

    user = session.query(User).filter(User.telegram_id == user_id).first()
    if not user:
        user = User(telegram_id=user_id, username=username)
        session.add(user)
        session.commit()
        welcome_text = "Добро пожаловать в Alkometer!"
    else:
        welcome_text = "С возвращением в Alkometer!"

    session.close()

    # Вместо main_menu_keyboard() - используем inline-кнопки
    keyboard = [
        [InlineKeyboardButton("🍺 Добавить алкоголь", callback_data="add_alcohol")],
        [InlineKeyboardButton("📊 Просмотр отчёта", callback_data="report")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        text=f"{welcome_text}\nПожалуйста, выбери опцию:",
        reply_markup=reply_markup
    )

# Регистрируем обработчик команды /start
start_handler = CommandHandler('start', start)
