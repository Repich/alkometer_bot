"""
Модуль add_alcohol.py

Реализует логику пошагового добавления информации об употреблении алкоголя:
1. Отображение списка популярных напитков + кнопка "Другой".
2. Если выбран существующий напиток — запрос объёма и цены.
3. Если выбран новый напиток — запрос названия и крепости, создание новой записи в AlcoholType;
   затем запрос объёма и цены, создание Consumption.

После завершения диалога пользователь возвращается в главное меню.
"""

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CommandHandler,
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

# Определяем состояния диалога
CHOOSE_FAV_DRINK, ASK_NAME, ASK_CONTENT, ASK_AMOUNT, ASK_PRICE = range(5)

async def add_alcohol_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг 1: Пользователь нажимает "Добавить алкоголь".
    Бот показывает список популярных напитков (top-6) + кнопку "Другой".
    """
    logger.info("Пользователь начал добавление алкоголя.")

    session = SessionLocal()
    try:
        # Получаем топ-6 самых популярных напитков (или меньше, если в базе их меньше 6)
        top_alcohols = get_top_alcohol_types(session, limit=6)

        # Формируем кнопки из списка напитков (по 3 в строке)
        keyboard = [
            [alc.name for alc in top_alcohols[i : i + 3]]
            for i in range(0, len(top_alcohols), 3)
        ]
        # Добавляем кнопку "Другой" для создания нового типа напитка
        keyboard.append(["Другой"])

        await update.message.reply_text(
            text="🎯 Выберите напиток из списка или нажмите 'Другой':",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )
        return CHOOSE_FAV_DRINK
    finally:
        session.close()

async def choose_fav_drink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг 2: Пользователь выбрал один из популярных напитков или "Другой".
    - Если "Другой" -> переходим к запросу названия нового напитка (ASK_NAME).
    - Если существующий напиток -> сохраняем его ID и переходим к запросу объёма (ASK_AMOUNT).
    """
    user_input = update.message.text.strip()

    if user_input == "Другой":
        await update.message.reply_text(
            text="📝 Введите название нового напитка:",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_NAME

    # Поиск напитка в базе данных
    session = SessionLocal()
    try:
        alcohol_type = get_alcohol_type_by_name(session, user_input)
        if not alcohol_type:
            await update.message.reply_text(
                "⚠️ Напиток не найден! Выберите из списка или нажмите 'Другой'."
            )
            return CHOOSE_FAV_DRINK

        context.user_data['alcohol_type_id'] = alcohol_type.id
        context.user_data['alcohol_name'] = alcohol_type.name

        # Переходим к запросу объёма (в литрах)
        await update.message.reply_text(
            text=f"📏 Сколько {alcohol_type.name} вы выпили? (в литрах)",
            reply_markup=ReplyKeyboardRemove()
        )
        return ASK_AMOUNT
    finally:
        session.close()

async def ask_alcohol_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Шаг 3 (ASK_NAME -> ASK_CONTENT):
    Пользователь ввёл новое название напитка, теперь нужно запросить крепость (0..100).
    """
    context.user_data['alcohol_name'] = update.message.text.strip()
    await update.message.reply_text(
        text="📊 Введите крепость напитка (число от 0 до 100):"
    )
    return ASK_CONTENT

async def create_new_alcohol_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Создаёт новую запись в таблице AlcoholType для нового напитка.
    Затем переходим к запросу объёма (ASK_AMOUNT).
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
                f"Новый напиток '{new_alcohol.name}' (крепость: {content}%) добавлен в базу.\n"
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
    Шаг 4 (ASK_AMOUNT): пользователь вводит объём (в литрах).
    Затем переходим к запросу цены (ASK_PRICE).
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
    Шаг 5 (ASK_PRICE): пользователь вводит стоимость.
    Сохраняем запись Consumption (привязка к user_id = user.id, а не telegram_id),
    после этого возвращаем пользователя в главное меню (start).
    """
    session = SessionLocal()
    user = None  # Объявляем заранее, чтобы избежать NameError в except
    try:
        price_str = update.message.text.replace(',', '.')
        price = float(price_str)
        if price < 0:
            raise ValueError("Цена не может быть отрицательной")

        # Получаем / создаём объект User (с помощью user_service)
        telegram_id = update.effective_user.id
        username = update.effective_user.username

        user = get_user(session, telegram_id)
        if not user:
            user = create_user(session, telegram_id, username)

        # Логируем для диагностики
        logger.info(f"[DEBUG] Получен пользователь: user.id={user.id}, telegram_id={user.telegram_id}")

        alcohol_type_id = context.user_data['alcohol_type_id']
        alcohol_name = context.user_data['alcohol_name']
        amount = context.user_data['amount']

        logger.info(f"[DEBUG] Будем сохранять Consumption c user_id={user.id}, alcohol_type_id={alcohol_type_id}")

        consumption = Consumption(
            user_id=user.id,         # ВАЖНО: ставим user.id, а не telegram_id
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
        await update.message.reply_text(f"❌ Некорректная цена: {ve}. Введите положительное число (руб):")
        return ASK_PRICE
    except Exception as e:
        logger.error(f"Ошибка при сохранении Consumption: {e}")
        # При желании можно вывести дополнительный лог user, если успели создать
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

# Полный ConversationHandler, объединяющий все шаги диалога
add_alcohol_conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex(r'^Добавить алкоголь$'), add_alcohol_start)],
    states={
        CHOOSE_FAV_DRINK: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, choose_fav_drink)
        ],
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
