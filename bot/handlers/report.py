# bot/handlers/report.py

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from bot.utils.db import SessionLocal
from bot.models.user import User
from bot.services.report_service import generate_report, render_chart_to_buffer
from bot.services.user_service import get_user

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик вывода отчета.
    """
    session = SessionLocal()
    try:
        telegram_id = update.effective_user.id
        user = get_user(session, telegram_id)
        if not user:
            await update.message.reply_text("Сначала введите /start для регистрации.")
            return

        text_report, report_data = generate_report(session, user)
        await update.message.reply_text(text_report)

        # Если report_data не None — значит есть что рисовать
        if report_data is not None and len(report_data) > 0:
            buf = render_chart_to_buffer(report_data)
            # Отправляем как фото
            await update.message.reply_photo(photo=buf, caption="График вашего потребления")
    finally:
        session.close()


# Регистрация обработчика команды /report
report_handler = CommandHandler('report', report)
