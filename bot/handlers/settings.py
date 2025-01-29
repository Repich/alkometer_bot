# bot/handlers/settings.py

from telegram.ext import CommandHandler, MessageHandler, ConversationHandler, ContextTypes
from telegram.ext.filters import Regex, Text, Command
from telegram import Update, ReplyKeyboardRemove
from bot.services.user_service import get_user, create_user, update_user_units, update_user_daily_goal
from bot.utils.db import SessionLocal

# Стадии разговора
CHOOSING, TYPING_REPLY = range(2)


async def settings_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Настройки:\nВыберите опцию:",
        reply_markup=settings_menu_keyboard(),
    )
    return CHOOSING


async def settings_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_choice = update.message.text
    context.user_data['choice'] = user_choice

    if user_choice == 'Единицы измерения':
        await update.message.reply_text(
            'Введите предпочитаемые единицы измерения (например, "шт", "литры"):',
            reply_markup=ReplyKeyboardRemove(),
        )
        return TYPING_REPLY
    elif user_choice == 'Цель по потреблению':
        await update.message.reply_text(
            'Введите вашу цель по потреблению алкоголя за день (например, "5 шт"):',
            reply_markup=ReplyKeyboardRemove(),
        )
        return TYPING_REPLY
    elif user_choice == 'Отмена':
        await update.message.reply_text('Возвращаемся в главное меню.', reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
        # Переходим обратно в главное меню
        # await main_menu(update, context)  # Вызов обработчика главного меню


async def settings_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    user_choice = context.user_data.get('choice')

    session = SessionLocal()
    user_id = update.effective_user.id
    user = get_user(session, user_id)

    if not user:
        user = create_user(session, user_id, update.effective_user.username)

    if user_choice == 'Единицы измерения':
        update_user_units(session, user, user_input)
        await update.message.reply_text(f'Единицы измерения обновлены на: {user_input}')
    elif user_choice == 'Цель по потреблению':
        try:
            goal = float(user_input)
            update_user_daily_goal(session, user, goal)
            await update.message.reply_text(f'Цель по потреблению установлена на: {goal}')
        except ValueError:
            await update.message.reply_text('Пожалуйста, введите числовое значение для цели.')

    session.close()
    return ConversationHandler.END


async def settings_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Настройки отменены.', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# Регистрация обработчика команды /settings с использованием ConversationHandler
settings_handler = ConversationHandler(
    entry_points=[CommandHandler('settings', settings_start)],
    states={
        CHOOSING: [MessageHandler(Regex('^(Единицы измерения|Цель по потреблению|Отмена)$'), settings_choice)],
        TYPING_REPLY: [MessageHandler(Text() & ~Command(), settings_received)],
    },
    fallbacks=[CommandHandler('cancel', settings_cancel)],
)
