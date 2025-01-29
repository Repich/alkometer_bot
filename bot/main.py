# bot/main.py

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)
from bot.handlers.start import start_handler
from bot.handlers.main_menu import main_menu_callback  # если у вас есть inline-меню
from bot.handlers.add_alcohol import (
    add_alcohol_conv_handler,
    inline_add_alcohol_callback
)
from bot.handlers.error_handler import error_handler_instance
from bot.config import TELEGRAM_BOT_TOKEN
from bot.logger import logger


def main():
    logger.info("Создание приложения бота")
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    logger.info("Регистрация обработчиков")

    # 1) Обработчик команды /start (из start.py):
    application.add_handler(start_handler)

    # 2) Если не нужны старые команды /report и /settings, убираем report_handler/settings_handler:
    # application.add_handler(report_handler)        # УДАЛЯЕМ или комментируем
    # application.add_handler(settings_handler)       # УДАЛЯЕМ или комментируем

    # 3) ConversationHandler для "Добавить алкоголь" (шаги крепость, объём, цена).
    #    Содержит CallbackQueryHandler или MessageHandler в states.
    application.add_handler(add_alcohol_conv_handler)

    # 4) CallbackQueryHandler для главного меню (inline):
    #    - pattern="^(add_alcohol|report|settings)$" или убираем pattern, если хотим ловить всё
    application.add_handler(
        CallbackQueryHandler(main_menu_callback, pattern="^(add_alcohol|report|settings)$")
    )

    # 6) Обработчик ошибок
    application.add_error_handler(error_handler_instance)

    logger.info("Запуск бота")
    application.run_polling()


if __name__ == "__main__":
    logger.info("Запуск main()")
    main()
