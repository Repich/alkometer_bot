# bot/services/user_service.py

from bot.utils.db import SessionLocal
from bot.models.user import User
from sqlalchemy.orm import Session
from typing import Optional


def get_user(session: Session, telegram_id: int) -> Optional[User]:
    """Получает пользователя по Telegram ID."""
    return session.query(User).filter(User.telegram_id == telegram_id).first()


def create_user(session: Session, telegram_id: int, username: str) -> User:
    """Создает нового пользователя."""
    user = User(telegram_id=telegram_id, username=username)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user_units(session: Session, user: User, units: str):
    """Обновляет единицы измерения пользователя."""
    user.units = units
    session.commit()


def update_user_daily_goal(session: Session, user: User, daily_goal: float):
    """Обновляет ежедневную цель потребления алкоголя пользователя."""
    user.daily_goal = daily_goal
    session.commit()
