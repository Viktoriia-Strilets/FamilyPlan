from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import models, schemas


def get_all_reports(db: Session, family_id: int):
    return (
        db.query(models.ExpenseReportModel)
        .filter(models.ExpenseReportModel.family_id == family_id)
        .order_by(models.ExpenseReportModel.period)
        .all()
    )


def create_report(
    db: Session,
    report: schemas.ReportCreate,
    family_id: int
):
    db_report = models.ExpenseReportModel(
        family_id=family_id,
        period=report.period,
        total_spent=report.total_spent,
        recommendations_text=report.recommendations_text
    )

    db.add(db_report)
    db.commit()
    db.refresh(db_report)

    return db_report


def delete_report(
    db: Session,
    report_id: int,
    family_id: int
):
    report = (
        db.query(models.ExpenseReportModel)
        .filter(
            models.ExpenseReportModel.id == report_id,
            models.ExpenseReportModel.family_id == family_id
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=404,
            detail="Звіт не знайдено"
        )

    db.delete(report)
    db.commit()

    return {
        "message": f"Звіт з ID {report_id} успішно видалено"
    }