
from datetime import datetime, timezone
from typing import List

import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app import models, schemas
from app.services.item_service import get_family_item
from app.services.budget_client import (
    send_purchase_to_budget,
    complete_planned_expense,
)

router = APIRouter(tags=["Shopping Items"])


@router.get(
    "/items",
    response_model=List[schemas.ShoppingItemResponse]
)
def get_items(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return (
        db.query(models.ShoppingItemModel)
        .filter(
            models.ShoppingItemModel.family_id
            == current_user["family_id"]
        )
        .order_by(
            models.ShoppingItemModel.is_purchased.asc(),
            models.ShoppingItemModel.created_at.desc()
        )
        .all()
    )


@router.post(
    "/items",
    response_model=schemas.ShoppingItemResponse,
    status_code=status.HTTP_201_CREATED
)
def create_item(
    item: schemas.ShoppingItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    username = current_user.get("username")

    if not username:
        raise HTTPException(
            status_code=401,
            detail="У токені відсутнє ім'я користувача. Повторно авторизуйтеся."
        )

    db_item = models.ShoppingItemModel(
        family_id=current_user["family_id"],
        created_by=username,
        name=item.name.strip(),
        quantity=item.quantity,
        category=item.category,
        estimated_price=item.estimated_price,
        planned_date=item.planned_date,
        is_purchased=False
    )

    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return db_item


@router.put(
    "/items/{item_id}",
    response_model=schemas.ShoppingItemResponse
)
def update_item(
    item_id: int,
    item_update: schemas.ShoppingItemUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    item = get_family_item(
        item_id,
        current_user["family_id"],
        db
    )
    if item.source_expense_id is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Цей товар пов'язаний із запланованою витратою Budget. "
                "Редагуйте його через розділ бюджету."
            )
        )

    update_data = item_update.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        update_data["name"] = update_data["name"].strip()

    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item


@router.patch(
    "/items/{item_id}/buy",
    response_model=schemas.ShoppingItemResponse
)
async def mark_item_as_purchased(
    item_id: int,
    purchase: schemas.PurchaseUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    item = get_family_item(
        item_id,
        current_user["family_id"],
        db
    )

    if item.is_purchased:
        raise HTTPException(
            status_code=400,
            detail="Товар уже позначений як придбаний"
        )

    actual_price = (
        purchase.actual_price
        if purchase is not None
        else None
    )

    if actual_price is not None and actual_price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Фактична ціна повинна бути більшою за нуль"
        )

    purchase_date = datetime.now(timezone.utc)

    # Синхронізація з Budget потрібна лише тоді,
    # коли є сума для створення або оновлення витрати.
    try:
        if item.source_expense_id is not None:
            # Товар створений із запланованої витрати.
            # Якщо фактичну ціну не вказано, використовуємо
            # попередньо задану орієнтовну ціну.
            budget_amount = actual_price

            if budget_amount is None:
                budget_amount = item.estimated_price

            if budget_amount is None:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Для завершення запланованої витрати "
                        "потрібна фактична або орієнтовна ціна"
                    )
                )

            await complete_planned_expense(
                expense_id=item.source_expense_id,
                purchase_id=item.id,
                family_id=item.family_id,
                amount=float(budget_amount),
                date=purchase_date.isoformat()
            )

        elif actual_price is not None:
            # Звичайний товар Shopping.
            # Без фактичної ціни не створюємо витрату в Budget.
            await send_purchase_to_budget(
                purchase_id=item.id,
                family_id=item.family_id,
                email=current_user["email"],
                username=(
                    current_user.get("username")
                    or item.created_by
                ),
                title=item.name,
                amount=float(actual_price),
                category=item.category or "Загальні",
                date=purchase_date.isoformat()
            )

    except HTTPException:
        raise

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=503,
            detail=(
                "Budget Service не відповідає. "
                "Покупку не позначено."
            )
        )

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Не вдалося зв'язатися з Budget Service. "
                "Покупку не позначено."
            )
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=(
                "Не вдалося синхронізувати покупку з бюджетом: "
                f"{str(e)}"
            )
        )

    # Зберігаємо покупку в Shopping Service.
    item.is_purchased = True
    item.purchased_at = purchase_date
    item.actual_price = actual_price

    try:
        db.commit()
        db.refresh(item)

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Витрату додано до бюджету, "
                "але не вдалося оновити список покупок. "
                "Повторна спроба не повинна створити дублікат."
            )
        )

    return item


@router.get(
    "/history",
    response_model=List[schemas.ShoppingItemResponse]
)
def get_purchase_history(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return (
        db.query(models.ShoppingItemModel)
        .filter(
            models.ShoppingItemModel.family_id
            == current_user["family_id"],
            models.ShoppingItemModel.is_purchased.is_(True)
        )
        .order_by(
            models.ShoppingItemModel.purchased_at.desc()
        )
        .all()
    )


@router.delete("/items/{item_id}")
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    item = get_family_item(
        item_id,
        current_user["family_id"],
        db
    )
    if item.source_expense_id is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Цей товар пов'язаний із запланованою витратою Budget. "
                "Видаліть відповідний план у розділі бюджету."
            )
        )

    db.delete(item)
    db.commit()

    return {
        "message": f"Товар з ID {item_id} успішно видалено"
    }
