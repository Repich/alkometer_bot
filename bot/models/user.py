# bot/models/user.py

from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from bot.utils.db import Base


class User(Base):
    """Модель пользователя."""

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String, nullable=True)
    units = Column(String, default='шт')  # Единицы измерения
    daily_goal = Column(Float, default=0.0)  # Цель по потреблению за день
    consumptions = relationship("Consumption", back_populates="user")
