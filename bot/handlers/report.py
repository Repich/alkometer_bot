# bot/handlers/report.py

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.db import SessionLocal
from bot.models.user import User
from bot.services.report_service import generate_report, render_chart_to_buffer
from bot.services.user_service import get_user

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        telegram_id = update.effective_user.id
        user = get_user(session, telegram_id)
        if not user:
            # Используем effective_message вместо message
            await update.effective_message.reply_text("Сначала введите /start для регистрации.")
            return

        text_report, report_data = generate_report(session, user)
        # Отправляем через effective_message
        await update.effective_message.reply_text(text_report)

        if report_data is not None and len(report_data) > 0:
            buf = render_chart_to_buffer(report_data)
            await update.effective_message.reply_photo(photo=buf, caption="График вашего потребления")
    finally:
        session.close()

# Регистрация обработчика команды /report
report_handler = CommandHandler('report', report)
