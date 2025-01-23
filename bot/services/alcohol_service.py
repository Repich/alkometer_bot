# bot/services/alcohol_service.py

from sqlalchemy.orm import Session
from bot.models.alcohol_type import AlcoholType
from bot.models.consumption import Consumption
from typing import List, Optional
from sqlalchemy import func


def get_alcohol_type_by_name(session: Session, name: str) -> Optional[AlcoholType]:
    return session.query(AlcoholType).filter(AlcoholType.name.ilike(name)).first()

def create_alcohol_type(session: Session, name: str, alcohol_content: float = 0.0, volume_per_unit: float = 0.5) -> AlcoholType:
    alcohol_type = AlcoholType(name=name, alcohol_content=alcohol_content)
    session.add(alcohol_type)
    session.commit()
    session.refresh(alcohol_type)
    return alcohol_type

def get_top_alcohol_types(session: Session, limit: int = 6) -> List[AlcoholType]:
    """
    Возвращает список самых популярных (по сумме amount) напитков.
    При равенстве сумм можно сортировать по алфавиту.
    """
    # Делаем JOIN Consumptions, группируем по alcohol_types.id
    # Суммируем consumption.amount, сортируем по убыванию
    subquery = (
        session.query(
            Consumption.alcohol_type_id,
            func.sum(Consumption.amount).label('total_amount')
        )
        .group_by(Consumption.alcohol_type_id)
        .subquery()
    )
    # Присоединяемся к alcohol_types, сортируем по total_amount
    query = (
        session.query(AlcoholType)
        .join(subquery, subquery.c.alcohol_type_id == AlcoholType.id, isouter=True)
        .order_by(subquery.c.total_amount.desc().nullslast())  # самые большие суммы первыми
        .limit(limit)
    )
    return query.all()
