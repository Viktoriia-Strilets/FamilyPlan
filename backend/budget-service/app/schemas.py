
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreateUpdate(BaseModel):
    total_planned_budget: float = Field(gt=0)
    currency: Optional[str] = "UAH"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExpenseCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    category: Optional[str] = "Загальні"
    is_planned: int = Field(default=0, ge=0, le=1)
    date: Optional[datetime] = None


class ExpenseResponse(ExpenseCreate):
    id: int
    budget_id: int
    user_id: int
    username: Optional[str] = None
    source_purchase_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class BudgetSummaryResponse(BaseModel):
    id: int
    family_id: int

    total_planned_budget: float
    total_spent: float
    total_planned_expenses: float
    remaining_budget: float

    currency: str

    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    expenses: List[ExpenseResponse]

    model_config = ConfigDict(from_attributes=True)

class ShoppingPurchaseCreate(BaseModel):
    purchase_id: int
    family_id: int
    email: str
    username: str
    title: str
    amount: float = Field(gt=0)
    category: Optional[str] = "Загальні"
    date: datetime

class PlannedExpensePurchaseUpdate(BaseModel):
    expense_id: int
    purchase_id: int
    family_id: int
    amount: float = Field(gt=0)
    date: datetime

class PlannedExpenseSyncItem(BaseModel):
    id: int
    budget_id: int
    title: str
    amount: float
    category: Optional[str] = "Загальні"
    date: Optional[datetime] = None
    user_id: int
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class BudgetSyncPeriod(BaseModel):
    id: int
    family_id: int
    total_planned_budget: float
    total_spent: float
    total_planned_expenses: float
    remaining_budget: float
    remaining_after_plans: float
    currency: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ShoppingBudgetSyncResponse(BaseModel):
    family_id: int
    budgets: List[BudgetSyncPeriod]
    planned_expenses: List[PlannedExpenseSyncItem]