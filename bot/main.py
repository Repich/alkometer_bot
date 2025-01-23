# bot/main.py

from telegram.ext import ApplicationBuilder
from bot.handlers.start import start_handler
from bot.handlers.add_alcohol import add_alcohol_conv_handler
from bot.handlers.report import report_handler
from bot.handlers.settings import settings_handler
from bot.handlers.main_menu import main_menu_handler
from bot.handlers.error_handler import error_handler_instance
from bot.config import TELEGRAM_BOT_TOKEN
from bot.logger import logger

def main():
    logger.info("Создание приложения бота")
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    logger.info("Регистрация обработчиков")

    application.add_handler(start_handler)
    application.add_handler(report_handler)
    application.add_handler(settings_handler)

    # Регистрируем ConversationHandler для "Добавить алкоголь"
    application.add_handler(add_alcohol_conv_handler)

    # Регистрируем обработчик главного меню
    application.add_handler(main_menu_handler)

    application.add_error_handler(error_handler_instance)

    logger.info("Запуск бота")
    application.run_polling()

if __name__ == "__main__":
    logger.info("Запуск main()")
    main()
