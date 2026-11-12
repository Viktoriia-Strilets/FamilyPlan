from sqlalchemy.orm import Session

from app import models


def forecast_future_expenses(
    db: Session,
    family_id: int
):
    reports = (
        db.query(models.ExpenseReportModel)
        .filter(models.ExpenseReportModel.family_id == family_id)
        .order_by(models.ExpenseReportModel.period)
        .all()
    )

    if len(reports) < 2:
        last_spent = (
            reports[-1].total_spent
            if reports
            else 10000.0
        )

        predicted = last_spent * 1.05

        return {
            "period": "Наступний місяць",
            "predicted_amount": round(predicted, 2),
            "basis_description": (
                "Прогноз на основі останнього періоду "
                "з урахуванням коефіцієнта 5%"
            )
        }

    total_historical = sum(
        report.total_spent for report in reports
    )

    average_spent = total_historical / len(reports)

    previous_spent = reports[-2].total_spent
    last_spent = reports[-1].total_spent

    trend_factor = (
        last_spent / previous_spent
        if previous_spent > 0
        else 1.0
    )

    predicted_amount = average_spent * (
        (trend_factor + 1.0) / 2.0
    )

    return {
        "period": "Наступний місяць",
        "predicted_amount": round(predicted_amount, 2),
        "basis_description": (
            f"Бізнес-аналіз на основі {len(reports)} "
            "попередніх звітів із розрахунком тренду."
        )
    }