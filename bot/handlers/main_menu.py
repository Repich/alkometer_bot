# bot/handlers/main_menu.py

from telegram import Update
from telegram.ext import MessageHandler, filters, ContextTypes
from bot.handlers.report import report
from bot.handlers.settings import settings_start

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == 'Просмотр отчёта':
        await report(update, context)
    elif text == 'Настройки':
        await settings_start(update, context)
    else:
        await update.message.reply_text("Пожалуйста, выберите опцию из меню.")

main_menu_handler = MessageHandler(
    filters.Regex('^(Просмотр отчёта|Настройки)$'),
    main_menu
)
