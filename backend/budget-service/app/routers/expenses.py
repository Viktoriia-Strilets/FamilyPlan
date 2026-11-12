
import os
import secrets

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.services.budget_service import normalize_dt
from app.models import UserModel

router = APIRouter(
    prefix="/budgets/expenses",
    tags=["Expenses"]
)


@router.post("", response_model=schemas.ExpenseResponse)
def add_expense_or_plan(
    data: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    if not current_user.family_id:
        raise HTTPException(
            status_code=400,
            detail="Користувач не належить до жодної родини"
        )

    if data.amount is None or data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Сума витрати повинна бути більшою за нуль"
        )

    expense_date = normalize_dt(data.date or datetime.utcnow())

    budgets = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.family_id == current_user.family_id
    ).all()

    selected_budget = None

    for budget in budgets:
        start = normalize_dt(budget.start_date)
        end = normalize_dt(budget.end_date)

        if start and end and start <= expense_date <= end:
            selected_budget = budget
            break

    if not selected_budget:
        raise HTTPException(
            status_code=400,
            detail="Для цієї дати не знайдено бюджетного періоду"
        )

    expense = models.ExpenseModel(
        budget_id=selected_budget.id,
        user_id=current_user.id,
        username=current_user.username,
        title=data.title.strip(),
        amount=data.amount,
        category=data.category or "Загальні",
        is_planned=data.is_planned,
        date=expense_date
    )

    try:
        db.add(expense)
        db.commit()
        db.refresh(expense)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не вдалося додати витрату або план"
        )

    return expense


@router.delete("/{expense_id}")
def delete_expense_or_plan(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    if not current_user.family_id:
        raise HTTPException(
            status_code=400,
            detail="Користувач не належить до жодної родини"
        )

    expense = db.query(
        models.ExpenseModel
    ).join(
        models.FamilyBudgetModel,
        models.ExpenseModel.budget_id == models.FamilyBudgetModel.id
    ).filter(
        models.ExpenseModel.id == expense_id,
        models.FamilyBudgetModel.family_id == current_user.family_id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=404,
            detail="Витрату не знайдено"
        )

    if expense.source_purchase_id is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "Цю витрату створено автоматично зі списку покупок. "
                "Змініть або видаліть відповідну покупку."
            )
        )
    try:
        db.delete(expense)
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не вдалося видалити витрату або план"
        )

    return {
        "message": "Витрату або план успішно видалено"
    }

@router.post(
    "/from-shopping",
    response_model=schemas.ExpenseResponse
)
def create_expense_from_shopping(
    data: schemas.ShoppingPurchaseCreate,
    db: Session = Depends(get_db),
    x_internal_api_key: str = Header(default="")
):
    expected_key = os.getenv("INTERNAL_API_KEY", "")

    if not expected_key or not secrets.compare_digest(
        x_internal_api_key,
        expected_key
    ):
        raise HTTPException(
            status_code=403,
            detail="Доступ заборонено"
        )

    if data.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Сума покупки повинна бути більшою за нуль"
        )

    # Перевірка на повторну покупку.
    existing_expense = db.query(
        models.ExpenseModel
    ).filter(
        models.ExpenseModel.source_purchase_id == data.purchase_id
    ).first()

    if existing_expense:
        return existing_expense

    # Перевірка або створення користувача в локальній БД.
    user = db.query(UserModel).filter(
        UserModel.email == data.email
    ).first()

    if not user:
        user = UserModel(
            email=data.email,
            username=data.username,
            family_id=data.family_id
        )
        db.add(user)
        db.flush()
    else:
        user.username = data.username
        user.family_id = data.family_id

    # Приводимо дату до UTC без timezone,
    # оскільки в бюджетній БД використовується DateTime без timezone.
    expense_date = data.date

    if expense_date.tzinfo is not None:
        expense_date = expense_date.astimezone(
            timezone.utc
        ).replace(tzinfo=None)

    # Знаходимо бюджетний період родини.
    matching_budget = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.family_id == data.family_id,
        models.FamilyBudgetModel.start_date <= expense_date,
        models.FamilyBudgetModel.end_date >= expense_date
    ).first()

    if not matching_budget:
        raise HTTPException(
            status_code=400,
            detail="На дату покупки не знайдено бюджетного періоду"
        )

    expense = models.ExpenseModel(
        budget_id=matching_budget.id,
        user_id=user.id,
        username=user.username,
        title=data.title,
        amount=data.amount,
        category=data.category or "Загальні",
        is_planned=0,
        date=expense_date,
        source_purchase_id=data.purchase_id
    )

    try:
        db.add(expense)
        db.commit()
        db.refresh(expense)

    except Exception:
        db.rollback()

        # Перевіряємо, чи інший паралельний запит
        # уже створив витрату для цієї покупки.
        existing_expense = db.query(
            models.ExpenseModel
        ).filter(
            models.ExpenseModel.source_purchase_id == data.purchase_id
        ).first()

        if existing_expense:
            return existing_expense

        raise HTTPException(
            status_code=500,
            detail="Не вдалося створити витрату з покупки"
        )

    return expense


@router.post("/complete-planned-from-shopping")
def complete_planned_expense_from_shopping(
    data: schemas.PlannedExpensePurchaseUpdate,
    internal_key: str = Header(
        default="",
        alias="X-Internal-Api-Key"
    ),
    db: Session = Depends(get_db)
):
    expected_key = os.getenv("INTERNAL_API_KEY", "")

    if (
        not expected_key
        or not internal_key
        or not secrets.compare_digest(internal_key, expected_key)
    ):
        raise HTTPException(
            status_code=403,
            detail="Недійсний внутрішній API-ключ"
        )

    expense = db.query(models.ExpenseModel).join(
        models.FamilyBudgetModel,
        models.ExpenseModel.budget_id == models.FamilyBudgetModel.id
    ).filter(
        models.ExpenseModel.id == data.expense_id,
        models.FamilyBudgetModel.family_id == data.family_id
    ).first()

    if not expense:
        raise HTTPException(
            status_code=404,
            detail="Заплановану витрату не знайдено"
        )

    # Повторний запит після успішної операції не створює дублікат.
    if int(expense.is_planned) == 0:
        if expense.source_purchase_id == data.purchase_id:
            return expense

        raise HTTPException(
            status_code=409,
            detail="Ця витрата вже була завершена іншою покупкою"
        )

    if expense.source_purchase_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Запланована витрата вже пов'язана з покупкою"
        )

    expense_date = normalize_dt(data.date)

    matching_budget = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.family_id == data.family_id,
        models.FamilyBudgetModel.start_date <= expense_date,
        models.FamilyBudgetModel.end_date >= expense_date
    ).first()

    if not matching_budget:
        raise HTTPException(
            status_code=400,
            detail="На дату покупки немає бюджетного періоду родини"
        )

    expense.budget_id = matching_budget.id
    expense.amount = data.amount
    expense.date = expense_date
    expense.is_planned = 0
    expense.source_purchase_id = data.purchase_id

    try:
        db.commit()
        db.refresh(expense)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не вдалося оновити заплановану витрату"
        )

    return expense
