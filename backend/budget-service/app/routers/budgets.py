
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.dependencies import check_family_head
from app.services.budget_service import (
    validate_budget_dates,
    check_budget_overlap,
    calculate_budget_summary,
)


router = APIRouter(
    prefix="/budgets",
    tags=["Budgets"]
)


@router.post("", response_model=schemas.BudgetSummaryResponse)
def create_budget(
    data: schemas.BudgetCreateUpdate,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    check_family_head(current_user)

    if data.total_planned_budget is None or data.total_planned_budget <= 0:
        raise HTTPException(
            status_code=400,
            detail="Сума бюджету повинна бути більшою за нуль"
        )

    start_new, end_new = validate_budget_dates(
        data.start_date,
        data.end_date
    )

    check_budget_overlap(
        db,
        current_user.family_id,
        start_new,
        end_new
    )

    new_budget = models.FamilyBudgetModel(
        family_id=current_user.family_id,
        total_planned_budget=data.total_planned_budget,
        currency=data.currency or "UAH",
        start_date=start_new,
        end_date=end_new
    )

    try:
        db.add(new_budget)
        db.commit()
        db.refresh(new_budget)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не вдалося створити бюджет"
        )

    return calculate_budget_summary(new_budget, db)


@router.get("", response_model=List[schemas.BudgetSummaryResponse])
def get_family_budgets(
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    if not current_user.family_id:
        raise HTTPException(
            status_code=400,
            detail="Користувач не належить до родини"
        )

    budgets = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.family_id == current_user.family_id
    ).order_by(
        models.FamilyBudgetModel.start_date.asc()
    ).all()

    return [
        calculate_budget_summary(budget, db)
        for budget in budgets
    ]

@router.get(
    "/internal/family/{family_id}/shopping-sync",
    response_model=schemas.ShoppingBudgetSyncResponse
)
def get_family_shopping_sync(
    family_id: int,
    db: Session = Depends(get_db),
    internal_key: str = Header(
        default="",
        alias="X-Internal-Api-Key"
    )
):
    # Перевірка внутрішнього API-ключа.
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

    # Отримуємо бюджетні періоди родини.
    budgets = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.family_id == family_id
    ).order_by(
        models.FamilyBudgetModel.start_date.asc()
    ).all()

    budget_results = []
    planned_expenses = []

    for budget in budgets:
        expenses = db.query(
            models.ExpenseModel
        ).filter(
            models.ExpenseModel.budget_id == budget.id
        ).all()

        total_spent = sum(
            float(expense.amount or 0)
            for expense in expenses
            if int(expense.is_planned or 0) == 0
        )

        total_planned = sum(
            float(expense.amount or 0)
            for expense in expenses
            if int(expense.is_planned or 0) == 1
        )

        total_budget = float(
            budget.total_planned_budget or 0
        )

        remaining_budget = total_budget - total_spent

        remaining_after_plans = (
            remaining_budget - total_planned
        )

        budget_results.append({
            "id": budget.id,
            "family_id": budget.family_id,
            "total_planned_budget": total_budget,
            "total_spent": total_spent,
            "total_planned_expenses": total_planned,
            "remaining_budget": remaining_budget,
            "remaining_after_plans": remaining_after_plans,
            "currency": budget.currency or "UAH",
            "start_date": budget.start_date,
            "end_date": budget.end_date
        })

        # У Shopping передаємо тільки ще не здійснені плани.
        for expense in expenses:
            if int(expense.is_planned or 0) != 1:
                continue

            planned_expenses.append({
                "id": expense.id,
                "budget_id": expense.budget_id,
                "title": expense.title,
                "amount": float(expense.amount),
                "category": expense.category or "Загальні",
                "date": expense.date,
                "user_id": expense.user_id,
                "username": expense.username
            })

    return {
        "family_id": family_id,
        "budgets": budget_results,
        "planned_expenses": planned_expenses
    }


@router.put("/{budget_id}", response_model=schemas.BudgetSummaryResponse)
def update_specific_budget(
    budget_id: int,
    data: schemas.BudgetCreateUpdate,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    check_family_head(current_user)

    budget = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.id == budget_id,
        models.FamilyBudgetModel.family_id == current_user.family_id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Бюджет не знайдено"
        )

    if data.total_planned_budget is None or data.total_planned_budget <= 0:
        raise HTTPException(
            status_code=400,
            detail="Сума бюджету повинна бути більшою за нуль"
        )

    start_new, end_new = validate_budget_dates(
        data.start_date,
        data.end_date
    )

    check_budget_overlap(
        db,
        current_user.family_id,
        start_new,
        end_new,
        exclude_budget_id=budget_id
    )

    budget.total_planned_budget = data.total_planned_budget
    budget.currency = data.currency or budget.currency or "UAH"
    budget.start_date = start_new
    budget.end_date = end_new

    try:
        db.commit()
        db.refresh(budget)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не вдалося оновити бюджет"
        )

    return calculate_budget_summary(budget, db)


@router.delete("/{budget_id}")
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    check_family_head(current_user)

    budget = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.id == budget_id,
        models.FamilyBudgetModel.family_id == current_user.family_id
    ).first()

    if not budget:
        raise HTTPException(
            status_code=404,
            detail="Бюджет не знайдено"
        )

    has_shopping_purchases = db.query(
        models.ExpenseModel
    ).filter(
        models.ExpenseModel.budget_id == budget_id,
        models.ExpenseModel.source_purchase_id.isnot(None)
    ).first()

    if has_shopping_purchases:
        raise HTTPException(
            status_code=409,
            detail=(
                "Неможливо видалити бюджетний період, "
                "оскільки він містить покупки зі списку Shopping."
            )
        )

    try:
        db.query(models.ExpenseModel).filter(
            models.ExpenseModel.budget_id == budget_id
        ).delete(synchronize_session=False)

        db.delete(budget)
        db.commit()

        return {
            "message": (
                "Бюджет та всі пов'язані витрати й плани "
                "успішно видалено"
            )
        }

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Помилка під час видалення бюджету"
        )



@router.put(
    "/expenses/{expense_id}",
    response_model=schemas.ExpenseResponse
)
def update_expense_or_plan(
    expense_id: int,
    data: schemas.ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: models.UserModel = Depends(get_current_user)
):
    if not current_user.family_id:
        raise HTTPException(
            status_code=400,
            detail="Користувач не належить до родини"
        )

    expense = db.query(models.ExpenseModel).join(
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

    # Автоматичні фактичні витрати редагуються через Shopping.
    if expense.source_purchase_id is not None or int(expense.is_planned) == 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "Фактичну витрату не можна редагувати окремо. "
                "Змініть відповідну покупку у списку Shopping."
            )
        )

    expense_date = normalize_dt(data.date or expense.date)

    if expense_date is None:
        raise HTTPException(
            status_code=400,
            detail="Потрібно вказати дату витрати"
        )

    matching_budget = db.query(
        models.FamilyBudgetModel
    ).filter(
        models.FamilyBudgetModel.family_id == current_user.family_id,
        models.FamilyBudgetModel.start_date <= expense_date,
        models.FamilyBudgetModel.end_date >= expense_date
    ).first()

    if not matching_budget:
        raise HTTPException(
            status_code=400,
            detail="На вибрану дату немає бюджетного періоду цієї родини"
        )

    expense.budget_id = matching_budget.id
    expense.title = data.title.strip()
    expense.amount = data.amount
    expense.category = data.category or "Загальні"
    expense.date = expense_date

    # Запис залишається запланованим.
    expense.is_planned = 1

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