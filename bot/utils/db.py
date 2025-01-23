# bot/utils/db.py

print("Импортируется модуль bot.utils.db")

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Определение пути к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, '../../data/alkometer.db')}"

# Создание двигателя подключения к базе данных
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Необходимо для SQLite
)

# Создание сессии для взаимодействия с базой данных
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()
