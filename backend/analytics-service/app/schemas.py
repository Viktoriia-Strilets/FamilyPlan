from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class ReportCreate(BaseModel):
    period: str = Field(
        min_length=7,
        max_length=7,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$"
    )
    total_spent: float = Field(ge=0)
    recommendations_text: Optional[str] = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    family_id: int
    period: str
    total_spent: float
    recommendations_text: Optional[str] = None


class CategoryStatResponse(BaseModel):
    category: str
    total_amount: float
    percentage: float


class ForecastResponse(BaseModel):
    period: str
    predicted_amount: float
    basis_description: str