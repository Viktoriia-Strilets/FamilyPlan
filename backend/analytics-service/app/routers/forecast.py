from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services import forecast_service

router = APIRouter(
    prefix="/analytics",
    tags=["Forecast"]
)


@router.get(
    "/forecast",
    response_model=schemas.ForecastResponse
)
def forecast_future_expenses(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return forecast_service.forecast_future_expenses(
        db,
        current_user["family_id"]
    )