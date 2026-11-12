from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.dependencies import get_current_user
from app.services import report_service

router = APIRouter(
    prefix="/reports",
    tags=["Reports"]
)


@router.get("/", response_model=List[schemas.ReportResponse])
def get_reports(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return report_service.get_all_reports(
        db,
        current_user["family_id"]
    )


@router.post(
    "/",
    response_model=schemas.ReportResponse,
    status_code=status.HTTP_201_CREATED
)
def create_report(
    report: schemas.ReportCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return report_service.create_report(
        db,
        report,
        current_user["family_id"]
    )


@router.delete("/{report_id}")
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return report_service.delete_report(
        db,
        report_id,
        current_user["family_id"]
    )