# bot/services/report_service.py

import os
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from typing import Dict
from io import BytesIO

from sqlalchemy.orm import Session
from bot.models.user import User
from bot.models.consumption import Consumption
from bot.models.alcohol_type import AlcoholType


def generate_report(session: Session, user: User):
    """
    Формирует данные отчета и возвращает:
    - текст отчета (str)
    - словарь report_data для построения графика
    """
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    consumptions = (
        session.query(Consumption)
        .join(AlcoholType)
        .filter(Consumption.user_id == user.id)
        .filter(Consumption.timestamp >= seven_days_ago)
        .all()
    )

    if not consumptions:
        return "Вы не употребляли алкоголь за последние 7 дней.", None
        # Убедитесь, что report_data не пуст после фильтрации

    report_data: Dict[str, Dict[str, float]] = {}
    total_absolute = 0.0
    total_cost = 0.0

    for consumption in consumptions:
        alc_type = consumption.alcohol_type
        name = alc_type.name

        # Литры
        display_amount = consumption.amount
        # Абсолютный спирт
        absolute = consumption.amount * (alc_type.alcohol_content / 100.0)
        # Стоимость
        cost = consumption.price

        if name not in report_data:
            report_data[name] = {
                'display_amount': 0.0,
                'absolute': 0.0,
                'cost': 0.0
            }

        report_data[name]['display_amount'] += display_amount
        report_data[name]['absolute'] += absolute
        report_data[name]['cost'] += cost

        total_absolute += absolute
        total_cost += cost

    lines = ["📊 Отчёт за последние 7 дней:\n"]
    for name, data in report_data.items():
        lines.append(
            f"• {name}:\n"
            f"  └ Выпито: {data['display_amount']:.2f} л\n"
            f"  └ Чистый алкоголь: {data['absolute']:.2f} л\n"
            f"  └ Стоимость: {data['cost']:.2f} руб\n"
        )

    lines.append(f"\n🔻 Всего чистого алкоголя: {total_absolute:.2f} л")
    lines.append(f"🔻 Общие затраты: {total_cost:.2f} руб")

    text_report = "\n".join(lines)

    return text_report, report_data


def render_chart_to_buffer(report_data: Dict[str, Dict[str, float]]) -> BytesIO:
    """
    Строит столбчатую диаграмму (используя report_data)
    и возвращает объект BytesIO с картинкой.
    """
    buf = BytesIO()
    buf.seek(0)

    names = list(report_data.keys())
    values = [v['absolute'] for v in report_data.values()]

    plt.figure(figsize=(10, 6))
    plt.bar(names, values, color='#4B96E9')
    plt.title("Содержание чистого алкоголя по напиткам")
    plt.ylabel("Литры")
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()

    plt.savefig(buf, format='png')
    plt.close()

    buf.seek(0)
    return buf
