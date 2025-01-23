# bot/models/consumption.py
from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from bot.utils.db import Base

class Consumption(Base):
    __tablename__ = 'consumptions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    alcohol_type_id = Column(Integer, ForeignKey('alcohol_types.id'), nullable=False)
    amount = Column(Float, nullable=False)  # Литры (сколько выпил в этот раз)
    price = Column(Float, nullable=False)   # Стоимость (сколько стоило в этот раз)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="consumptions")
    alcohol_type = relationship("AlcoholType", back_populates="consumptions")
