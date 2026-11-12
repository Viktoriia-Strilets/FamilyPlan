
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user
from app import models, schemas


router = APIRouter(tags=["Recommendations"])


@router.get(
    "/recommendations",
    response_model=List[schemas.RecommendationResponse]
)
def get_shopping_recommendations(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Формує рекомендації на основі найчастіше придбаних товарів родини.
    """

    family_id = current_user["family_id"]

    frequent_items = (
        db.query(
            models.ShoppingItemModel.name,
            models.ShoppingItemModel.category,
            func.count(
                models.ShoppingItemModel.id
            ).label("count")
        )
        .filter(
            models.ShoppingItemModel.family_id == family_id,
            models.ShoppingItemModel.is_purchased.is_(True)
        )
        .group_by(
            models.ShoppingItemModel.name,
            models.ShoppingItemModel.category
        )
        .having(
            func.count(models.ShoppingItemModel.id) >= 2
        )
        .order_by(
            func.count(models.ShoppingItemModel.id).desc()
        )
        .limit(5)
        .all()
    )

    recommendations = []

    for item in frequent_items:
        recommendations.append({
            "title": f"Часта покупка: {item.name}",
            "description": (
                f"Категорія: {item.category or 'Загальні'}. "
                "Ви купували це вже кілька разів."
            ),
            "suggested_name": item.name,
            "category": item.category
        })

    if not recommendations:
        recommendations.append({
            "title": "Порада від системи",
            "description": (
                "Додайте базові товари (молоко, хліб, вода), "
                "щоб сформувати історію для розумних рекомендацій."
            ),
            "suggested_name": "Молоко",
            "category": "Продукти"
        })

    return recommendations
