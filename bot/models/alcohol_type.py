# bot/models/alcohol_type.py (или внутри models.py)
from sqlalchemy import Column, Integer, String, Float
from bot.utils.db import Base
from sqlalchemy.orm import relationship

class AlcoholType(Base):
    __tablename__ = 'alcohol_types'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    alcohol_content = Column(Float, default=0.0)  # Процент спирта (0..100)
    consumptions = relationship("Consumption", back_populates="alcohol_type")
