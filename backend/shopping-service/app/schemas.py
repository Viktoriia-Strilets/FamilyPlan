
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ShoppingItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: int = Field(default=1, ge=1)
    category: Optional[str] = None

    estimated_price: Optional[Decimal] = Field(
        default=None,
        ge=0
    )

    planned_date: Optional[datetime] = None


class ShoppingItemUpdate(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200
    )

    quantity: Optional[int] = Field(default=None, ge=1)
    category: Optional[str] = None

    estimated_price: Optional[Decimal] = Field(
        default=None,
        ge=0
    )

    planned_date: Optional[datetime] = None


class PurchaseUpdate(BaseModel):
    actual_price: Optional[Decimal] = Field(
        default=None,
        ge=0
    )


class ShoppingItemResponse(BaseModel):
    id: int
    family_id: int
    created_by: str

    name: str
    quantity: int
    category: Optional[str]

    estimated_price: Optional[Decimal]
    actual_price: Optional[Decimal]

    planned_date: Optional[datetime]
    is_purchased: bool
    purchased_at: Optional[datetime]

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationResponse(BaseModel):
    title: str
    description: str
    suggested_name: str
    category: Optional[str] = None


class ReminderResponse(BaseModel):
    item_id: int
    level: str
    text: str
