# bot/models.py

print("Импортируется модуль bot.models")

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from bot.utils.db import Base
from datetime import datetime

class User(Base):
    """
    Модель пользователя.
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)

    consumptions = relationship("Consumption", back_populates="user")
    alcohol_types = relationship("AlcoholType", back_populates="user")


class AlcoholType(Base):
    __tablename__ = 'alcohol_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    alcohol_content = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    volume_per_unit = Column(Float, default=0.5)  # Добавлено новое поле

    # Убрать user_id и связь с User
    consumptions = relationship("Consumption", back_populates="alcohol_type")


class Consumption(Base):
    """
    Модель потребления алкоголя.
    """
    __tablename__ = 'consumptions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    alcohol_type_id = Column(Integer, ForeignKey('alcohol_types.id'), nullable=False)
    amount = Column(Float, nullable=False)  # Количество выпитого
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="consumptions")
    alcohol_type = relationship("AlcoholType", back_populates="consumptions")
