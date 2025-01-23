# bot/handlers/main_menu.py

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot.handlers.report import report
from bot.handlers.settings import settings_start
from bot.handlers.add_alcohol import inline_add_alcohol_start

async def main_menu_inline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отправляет сообщение с inline-кнопками для главного меню.
    """
    keyboard = [
        [InlineKeyboardButton("🍺 Добавить алкоголь", callback_data="add_alcohol")],
        [InlineKeyboardButton("📊 Просмотр отчёта", callback_data="report")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Если это вызов команды /start или /menu, update.message будет не None
    await update.message.reply_text("Главное меню (inline):", reply_markup=reply_markup)


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка нажатий на inline-кнопки главного меню.
    """
    query = update.callback_query
    data = query.data
    await query.answer()  # подтверждаем callback, чтобы Telegram не висел на "…"

    if data == "add_alcohol":
        # Запускаем inline-логику добавления алкоголя
        await inline_add_alcohol_start(query, context)
    elif data == "report":
        # Запускаем отчёт
        # Можем отредактировать сообщение или отправить новое
        # Здесь для примера отправим новый
        await report(query, context)
    elif data == "settings":
        await settings_start(query, context)
    else:
        await query.edit_message_text("Неизвестная команда.")

# Не нужен main_menu_handler с MessageHandler, так как теперь используем inline-кнопки.
# Вместо этого в main.py регистрируем:
# 1) Команду /menu (или /start) => main_menu_inline
# 2) CallbackQueryHandler => main_menu_callback
