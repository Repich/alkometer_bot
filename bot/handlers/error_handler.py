# bot/handlers/error_handler.py

from telegram import Update
from telegram.ext import ContextTypes
from bot.logger import logger


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок. Логирует ошибки и уведомляет пользователя."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # Пытаемся отправить сообщение пользователю об ошибке
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text('Произошла ошибка. Пожалуйста, попробуйте позже.')
        except Exception as e:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {e}")


# Создание экземпляра обработчика ошибок
error_handler_instance = error_handler
