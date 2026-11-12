
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models


from datetime import timezone


def normalize_dt(dt):
    if dt is None:
        return None

    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)

    return dt


def validate_budget_dates(start_date, end_date):
    start_new = normalize_dt(start_date)
    end_new = normalize_dt(end_date)

    if not start_new or not end_new:
        raise HTTPException(
            status_code=400,
            detail="Потрібно вказати початкову та кінцеву дату бюджету"
        )

    if start_new > end_new:
        raise HTTPException(
            status_code=400,
            detail="Початкова дата не може бути пізніше кінцевої"
        )

    return start_new, end_new


def check_budget_overlap(
    db: Session,
    family_id: int,
    start_new,
    end_new,
    exclude_budget_id=None
):
    query = db.query(models.FamilyBudgetModel).filter(
        models.FamilyBudgetModel.family_id == family_id
    )

    if exclude_budget_id is not None:
        query = query.filter(
            models.FamilyBudgetModel.id != exclude_budget_id
        )

    existing_budgets = query.all()

    for budget in existing_budgets:
        start_old = normalize_dt(budget.start_date)
        end_old = normalize_dt(budget.end_date)

        if start_old and end_old:
            if start_new <= end_old and end_new >= start_old:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"На цей період уже існує бюджет: "
                        f"{start_old:%Y-%m-%d} — "
                        f"{end_old:%Y-%m-%d}"
                    )
                )


def calculate_budget_summary(
    budget: models.FamilyBudgetModel,
    db: Session
):
    expenses = db.query(
        models.ExpenseModel
    ).filter(
        models.ExpenseModel.budget_id == budget.id
    ).order_by(
        models.ExpenseModel.date.desc()
    ).all()

    start = normalize_dt(budget.start_date)
    end = normalize_dt(budget.end_date)

    period_expenses = []

    for expense in expenses:
        expense_date = normalize_dt(expense.date)

        if start and end:
            if expense_date and start <= expense_date <= end:
                period_expenses.append(expense)
        else:
            period_expenses.append(expense)

    actual_expenses = [
        expense for expense in period_expenses
        if int(expense.is_planned) == 0
    ]

    planned_expenses = [
        expense for expense in period_expenses
        if int(expense.is_planned) == 1
    ]

    total_spent = sum(
        (expense.amount for expense in actual_expenses),
        0
    )

    total_planned_expenses = sum(
        (expense.amount for expense in planned_expenses),
        0
    )

    return {
        "id": budget.id,
        "family_id": budget.family_id,
        "total_planned_budget": budget.total_planned_budget,
        "total_spent": total_spent,
        "total_planned_expenses": total_planned_expenses,
        "remaining_budget": (
            budget.total_planned_budget - total_spent
        ),
        "currency": budget.currency,
        "start_date": budget.start_date,
        "end_date": budget.end_date,
        "expenses": expenses
    }
