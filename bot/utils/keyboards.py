# bot/utils/keyboards.py

from telegram import ReplyKeyboardMarkup


def main_menu_keyboard():
    """Создает клавиатуру для главного меню."""
    keyboard = [['Добавить алкоголь', 'Просмотр отчёта'], ['Настройки']]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)


def settings_menu_keyboard():
    """Создает клавиатуру для настроек."""
    keyboard = [['Единицы измерения', 'Цель по потреблению'], ['Отмена']]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
