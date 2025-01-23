# Например, скрипт fake_data.py

from bot.utils.db import engine, SessionLocal, Base
from bot.models.alcohol_type import AlcoholType

def create_base_types():
    Base.metadata.create_all(engine)
    session = SessionLocal()

    # Словарь: название -> процент алкоголя
    base_types = {
        "Водка": 40.0,
        "Виски": 40.0,
        "Пиво": 5.0,
        "Вино": 13.0,
        "Коньяк": 40.0,
        "Текила": 38.0,
    }

    for name, alc_percent in base_types.items():
        # Проверяем, нет ли уже такого типа
        exist = session.query(AlcoholType).filter_by(name=name).first()
        if exist is None:
            session.add(AlcoholType(name=name, alcohol_content=alc_percent))
    session.commit()
    session.close()

if __name__ == "__main__":
    create_base_types()
    print("База заполнена базовыми типами алкоголя.")
