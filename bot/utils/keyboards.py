# bot/utils/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def main_menu_inline_keyboard():
    """Создает inline-кнопки для главного меню."""
    keyboard = [
        [InlineKeyboardButton("🍺 Добавить алкоголь", callback_data="add_alcohol")],
        [InlineKeyboardButton("📊 Просмотр отчёта", callback_data="report")],
        [InlineKeyboardButton("⚙️ Настройки", callback_data="settings")]
    ]
    return InlineKeyboardMarkup(keyboard)

def settings_inline_keyboard():
    """Создает inline-кнопки для настроек (пример)."""
    keyboard = [
        [InlineKeyboardButton("Единицы измерения", callback_data="units")],
        [InlineKeyboardButton("Цель по потреблению", callback_data="daily_goal")],
        [InlineKeyboardButton("Отмена", callback_data="cancel_settings")]
    ]
    return InlineKeyboardMarkup(keyboard)
