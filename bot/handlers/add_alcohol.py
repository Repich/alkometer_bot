# bot/handlers/add_alcohol.py

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
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
    create_alcohol_type,
    get_top_alcohol_types
)
from bot.models.consumption import Consumption
from bot.handlers.start import start

# Состояния для ConversationHandler
(CHOOSE_FAV_DRINK, ASK_NAME, ASK_CONTENT, ASK_AMOUNT, ASK_PRICE) = range(5)


async def inline_add_alcohol_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    1) Показываем список популярных напитков + «Другой» (inline).
    2) Эта функция НЕ возвращает состояние ConversationHandler:
       – пользователь только видит кнопки.
    3) Следующий шаг (inline_add_alcohol_callback) вызывается, когда нажмут «fav:...»
       или «other_new_drink».
    """
    logger.info("Пользователь начал добавление алкоголя (inline).")

    query = update.callback_query  # Вызываемся из CallbackQueryHandler
    await query.answer()           # Убираем "..."

    chat_id = update.effective_chat.id

    session = SessionLocal()
    try:
        top_alcohols = get_top_alcohol_types(session, limit=6)
        buttons = []
        for alc in top_alcohols:
            # Для каждого напитка создаём кнопку callback_data="fav:<id>"
            buttons.append([InlineKeyboardButton(alc.name, callback_data=f"fav:{alc.id}")])

        # Кнопка "Другой"
        buttons.append([InlineKeyboardButton("Другой", callback_data="other_new_drink")])

        reply_markup = InlineKeyboardMarkup(buttons)

        await context.bot.send_message(
            chat_id=chat_id,
            text="🎯 Выберите напиток из списка или нажмите 'Другой':",
            reply_markup=reply_markup
        )
    finally:
        session.close()


async def inline_add_alcohol_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    2) Обработка нажатий "fav:<id>" или "other_new_drink".
       Здесь мы входим в ConversationHandler, возвращая ASK_AMOUNT или ASK_NAME.
    """
    query = update.callback_query
    await query.answer()

    data = query.data  # "fav:5" или "other_new_drink"
    logger.info(f"inline_add_alcohol_callback data={data}")

    if data.startswith("fav:"):
        # Пользователь выбрал существующий напиток
        alc_id_str = data.split(":")[1]
        alc_id = int(alc_id_str)
        context.user_data['alcohol_type_id'] = alc_id

        from bot.models.alcohol_type import AlcoholType
        session = SessionLocal()
        try:
            alc_obj = session.query(AlcoholType).get(alc_id)
            if alc_obj:
                context.user_data['alcohol_name'] = alc_obj.name
                # Спрашиваем количество (litre)
                await query.edit_message_text(f"📏 Сколько {alc_obj.name} вы выпили? (в литрах)")
                logger.info("Переход к состоянию ASK_AMOUNT")
                return ASK_AMOUNT
            else:
                await query.edit_message_text("⚠️ Напиток не найден в базе.")
                return ConversationHandler.END
        finally:
            session.close()

    elif data == "other_new_drink":
        # Просим ввести новое название
        await query.edit_message_text("📝 Введите название нового напитка:")
        return ASK_NAME

    else:
        await query.edit_message_text("Неизвестный выбор.")
        return ConversationHandler.END


async def ask_alcohol_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг (ASK_NAME -> ASK_CONTENT): пользователь ввёл новое название, теперь крепость (0..100).
    """
    logger.info("ask_alcohol_content вызывается")
    context.user_data['alcohol_name'] = update.message.text.strip()
    await update.message.reply_text("📊 Введите крепость напитка (0..100):")
    return ASK_CONTENT


async def create_new_alcohol_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Создаём новый тип в БД, затем спрашиваем количество (ASK_AMOUNT).
    """
    logger.info("create_new_alcohol_type вызывается")
    session = SessionLocal()
    try:
        content_str = update.message.text.replace(',', '.')
        content = float(content_str)
        if not (0 <= content <= 100):
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
    Шаг ASK_AMOUNT: ввод объёма (литров), потом спрашиваем цену (ASK_PRICE).
    """
    logger.info("ask_alcohol_volume вызывается")
    text = update.message.text.replace(',', '.')
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
        context.user_data['amount'] = amount
        logger.info(f"Количество сохранено: {amount}")
    except ValueError:
        logger.warning(f"Некорректный ввод объёма: {text}")
        await update.message.reply_text("❌ Введите положительное число (литры):")
        return ASK_AMOUNT

    logger.info("Переход к состоянию ASK_PRICE")
    await update.message.reply_text("💰 Введите стоимость (руб) для этого события:")
    return ASK_PRICE

async def save_consumption(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг ASK_PRICE: сохраняем всё в БД и выходим из разговора, возвращаясь в главное меню.
    """
    logger.info("save_consumption вызывается")
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

    # Возвращаем пользователя в главное меню
    await start(update, context)
    return ConversationHandler.END


# ConversationHandler: включаем per_message=True,
# чтобы гарантированно отслеживать сообщение после inline-callback
add_alcohol_conv_handler = ConversationHandler(
    entry_points=[
        # Используем паттерн, который ловит "fav:" с любыми символами после
        CallbackQueryHandler(inline_add_alcohol_callback, pattern=r"^fav:\d+|other_new_drink$")
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
    fallbacks=[
        CommandHandler('cancel', lambda u, c: ConversationHandler.END)
    ],
    per_chat=True
)
