# initialize_db.py
from bot.models.user import User
from bot.models.alcohol_type import AlcoholType  # Добавьте эту строку
from bot.models.consumption import Consumption
from bot.logger import logger

logger.info("Импортируется модуль initialize_db.py")

from bot.utils.db import Base, engine
from bot.models import User, AlcoholType, Consumption

def initialize_database():
    """
    Инициализирует базу данных, создавая все необходимые таблицы.
    """
    Base.metadata.create_all(engine)
    logger.info("База данных инициализирована.")

if __name__ == "__main__":
    initialize_database()
