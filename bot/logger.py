# bot/logger.py

import logging
import sys

# Создание логгера
logger = logging.getLogger('alkometer_bot')
logger.setLevel(logging.INFO)

# Создание обработчика для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Создание обработчика для записи в файл
file_handler = logging.FileHandler('bot.log')
file_handler.setLevel(logging.DEBUG)

# Создание форматтера и добавление его к обработчикам
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# Добавление обработчиков к логгеру
logger.addHandler(console_handler)
logger.addHandler(file_handler)

