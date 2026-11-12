
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import ShoppingItemModel


def get_family_item(
    item_id: int,
    family_id: int,
    db: Session
):
    item = (
        db.query(ShoppingItemModel)
        .filter(
            ShoppingItemModel.id == item_id,
            ShoppingItemModel.family_id == family_id
        )
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Товар не знайдено"
        )

    return item
