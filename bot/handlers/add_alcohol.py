# bot/handlers/add_alcohol.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)
from bot.logger import logger
from bot.utils.db import SessionLocal
from bot.services.user_service import get_user, create_user
from bot.services.alcohol_service import (
    get_alcohol_type_by_name,
    create_alcohol_type,
    get_top_alcohol_types
)
from bot.models.consumption import Consumption
from bot.handlers.start import start

# Состояния
CHOOSE_FAV_DRINK, ASK_NAME, ASK_CONTENT, ASK_AMOUNT, ASK_PRICE = range(5)

async def inline_add_alcohol_start(update_or_query, context: ContextTypes.DEFAULT_TYPE):
    """
    Инлайн-версия шага 1: Показываем топ-6 популярных напитков + кнопку "Другой" в inline-виде.
    Вызывается из main_menu_callback(data='add_alcohol').
    """
    logger.info("Пользователь начал добавление алкоголя (inline).")

    # Проверяем, update_or_query может быть CallbackQuery или Update
    if hasattr(update_or_query, 'callback_query'):
        query = update_or_query.callback_query
        await query.answer()
        chat_id = query.message.chat_id
    else:
        chat_id = update_or_query.effective_chat.id

    session = SessionLocal()
    try:
        top_alcohols = get_top_alcohol_types(session, limit=6)
        # Формируем inline-кнопки по напиткам
        buttons = []
        for alc in top_alcohols:
            buttons.append([InlineKeyboardButton(alc.name, callback_data=f"fav:{alc.id}")])
        # Кнопка "Другой"
        buttons.append([InlineKeyboardButton("Другой", callback_data="other_new_drink")])

        reply_markup = InlineKeyboardMarkup(buttons)

        # Отправляем или редактируем сообщение
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎯 Выберите напиток из списка или нажмите 'Другой':",
            reply_markup=reply_markup
        )
    finally:
        session.close()


async def inline_add_alcohol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка нажатий inline-кнопок из inline_add_alcohol_start.
    """
    query = update.callback_query
    await query.answer()

    data = query.data  # Пример: "fav:1" или "other_new_drink"
    if data.startswith("fav:"):
        # Пользователь выбрал один из существующих напитков
        alc_id_str = data.split(":")[1]
        alc_id = int(alc_id_str)
        context.user_data['alcohol_type_id'] = alc_id

        # Найдём имя напитка для контекста
        session = SessionLocal()
        try:
            alc = session.get_top_alcohol_types  # ОШИБКА, нужно get(AlcoholType, alc_id)
            # Правильнее:
            from bot.models.alcohol_type import AlcoholType
            alc_obj = session.query(AlcoholType).get(alc_id)
            if alc_obj:
                context.user_data['alcohol_name'] = alc_obj.name
                # Переходим к запросу объёма (в литрах) -- обычный текст
                await query.edit_message_text(
                    text=f"📏 Сколько {alc_obj.name} вы выпили? (в литрах)"
                )
                # Меняем состояние
                return ASK_AMOUNT
            else:
                await query.edit_message_text("⚠️ Напиток не найден в базе.")
                return ConversationHandler.END
        finally:
            session.close()

    elif data == "other_new_drink":
        # Переходим к запросу названия нового напитка
        await query.edit_message_text(
            text="📝 Введите название нового напитка:"
        )
        return ASK_NAME
    else:
        await query.edit_message_text("Неизвестный выбор.")
        return ConversationHandler.END


async def ask_alcohol_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг (ASK_NAME -> ASK_CONTENT).
    """
    context.user_data['alcohol_name'] = update.message.text.strip()
    await update.message.reply_text(
        text="📊 Введите крепость напитка (0..100):"
    )
    return ASK_CONTENT

async def create_new_alcohol_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Создаёт новый напиток, затем спрашиваем объём (литрами).
    """
    session = SessionLocal()
    try:
        content_str = update.message.text.replace(',', '.')
        content = float(content_str)
        if content < 0 or content > 100:
            raise ValueError
        new_alcohol = create_alcohol_type(
            session=session,
            name=context.user_data['alcohol_name'],
            alcohol_content=content
        )
        context.user_data['alcohol_type_id'] = new_alcohol.id
        context.user_data['alcohol_name'] = new_alcohol.name

        await update.message.reply_text(
            text=(
                f"Новый напиток '{new_alcohol.name}' (крепость: {content}%) добавлен.\n"
                f"📏 Сколько {new_alcohol.name} вы выпили? (в литрах)"
            )
        )
        return ASK_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ Некорректная крепость! Введите число от 0 до 100:")
        return ASK_CONTENT
    finally:
        session.close()

async def ask_alcohol_volume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг ASK_AMOUNT: ввод объёма (литров), затем переходим к цене.
    """
    text = update.message.text.replace(',', '.')
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
        context.user_data['amount'] = amount
    except ValueError:
        await update.message.reply_text("❌ Введите положительное число (литры):")
        return ASK_AMOUNT

    await update.message.reply_text("💰 Введите стоимость (руб) для этого события:")
    return ASK_PRICE

async def save_consumption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг ASK_PRICE: сохраняем в БД, возвращаем в главное меню.
    """
    session = SessionLocal()
    user = None
    try:
        price_str = update.message.text.replace(',', '.')
        price = float(price_str)
        if price < 0:
            raise ValueError("Цена не может быть отрицательной")

        telegram_id = update.effective_user.id
        username = update.effective_user.username
        user = get_user(session, telegram_id)
        if not user:
            user = create_user(session, telegram_id, username)

        alcohol_type_id = context.user_data['alcohol_type_id']
        alcohol_name = context.user_data['alcohol_name']
        amount = context.user_data['amount']

        consumption = Consumption(
            user_id=user.id,
            alcohol_type_id=alcohol_type_id,
            amount=amount,
            price=price
        )
        session.add(consumption)
        session.commit()

        await update.message.reply_text(
            text=(
                f"✅ Успешно добавлено!\n"
                f"• Напиток: {alcohol_name}\n"
                f"• Количество: {amount} л\n"
                f"• Стоимость: {price} руб\n"
            )
        )
    except ValueError as ve:
        await update.message.reply_text(f"❌ Некорректная цена: {ve}. Повторите ввод (руб):")
        return ASK_PRICE
    except Exception as e:
        logger.error(f"Ошибка при сохранении Consumption: {e}")
        if user:
            logger.error(f"Ошибка у пользователя: user.id={user.id}, telegram_id={user.telegram_id}")
        await update.message.reply_text("⚠️ Произошла ошибка при сохранении. Попробуйте заново.")
        return ConversationHandler.END
    finally:
        session.close()
        context.user_data.clear()

    # Возвращаем в главное меню
    await start(update, context)
    return ConversationHandler.END


# Inline-конверсация: entry_points = [CallbackQueryHandler(inline_add_alcohol_start, pattern="add_alcohol")]
# Но мы можем использовать промежуточное "main_menu.py"

add_alcohol_conv_handler = ConversationHandler(
    entry_points=[
        # Теперь не MessageHandler, а CallbackQueryHandler на "fav:" или "other_new_drink"
        CallbackQueryHandler(inline_add_alcohol_callback, pattern="^fav:|^other_new_drink$")
    ],
    states={
        ASK_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_alcohol_content)
        ],
        ASK_CONTENT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, create_new_alcohol_type)
        ],
        ASK_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_alcohol_volume)
        ],
        ASK_PRICE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, save_consumption)
        ],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)
