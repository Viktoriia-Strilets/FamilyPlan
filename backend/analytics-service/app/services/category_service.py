from sqlalchemy.orm import Session
from sqlalchemy import func

from app import models


def get_category_statistics(
    db: Session,
    period: str,
    family_id: int
):
    stats = (
        db.query(
            models.CategoryStatisticsModel.category,
            func.sum(
                models.CategoryStatisticsModel.total_amount
            ).label("total")
        )
        .filter(
            models.CategoryStatisticsModel.period == period,
            models.CategoryStatisticsModel.family_id == family_id
        )
        .group_by(models.CategoryStatisticsModel.category)
        .all()
    )

    if not stats:
        return []

    grand_total = sum(item.total for item in stats)

    return [
        {
            "category": category,
            "total_amount": float(total),
            "percentage": round(
                (total / grand_total) * 100 if grand_total > 0 else 0,
                2
            )
        }
        for category, total in stats
    ]