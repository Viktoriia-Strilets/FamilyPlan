
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app import models


router = APIRouter(tags=["Reminders"])


@router.get("/reminders")
def get_shopping_reminders(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Формує нагадування про заплановані та прострочені покупки.
    """

    family_id = current_user["family_id"]
    today_date = datetime.now(timezone.utc).date()

    active_items = (
        db.query(models.ShoppingItemModel)
        .filter(
            models.ShoppingItemModel.family_id == family_id,
            models.ShoppingItemModel.is_purchased.is_(False),
            models.ShoppingItemModel.planned_date.isnot(None)
        )
        .all()
    )

    reminders = []

    for item in active_items:
        if item.planned_date:
            item_date = (
                item.planned_date.date()
                if isinstance(item.planned_date, datetime)
                else item.planned_date
            )

            delta_days = (item_date - today_date).days

            if delta_days < 0:
                reminders.append({
                    "item_id": item.id,
                    "level": "danger",
                    "text": (
                        f"⚠️ Прострочено! Товар «{item.name}» "
                        f"мав бути куплений {item_date.strftime('%d.%m.%Y')}."
                    )
                })

            elif delta_days == 0:
                reminders.append({
                    "item_id": item.id,
                    "level": "warning",
                    "text": (
                        f"🔔 Нагадування: Товар «{item.name}» "
                        "заплановано купити сьогодні!"
                    )
                })

    return reminders
