from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services import category_service

router = APIRouter(
    prefix="/analytics/categories",
    tags=["Categories"]
)


@router.get(
    "/{period}",
    response_model=List[schemas.CategoryStatResponse]
)
def get_category_statistics(
    period: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return category_service.get_category_statistics(
        db,
        period,
        current_user["family_id"]
    )