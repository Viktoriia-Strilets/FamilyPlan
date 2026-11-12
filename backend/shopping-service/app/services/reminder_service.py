
import logging
import os

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app import models
from app.services.email_service import send_reminder_email


logger = logging.getLogger(__name__)


def get_local_planned_date(planned_date):
    """
    Перетворює дату покупки на локальну дату
    відповідно до часового поясу FamilyPlan.
    """

    timezone_name = os.getenv(
        "REMINDER_TIMEZONE",
        "Europe/Kyiv"
    )

    timezone = ZoneInfo(timezone_name)

    if planned_date.tzinfo is not None:
        return planned_date.astimezone(timezone).date()

    return planned_date.date()


def process_due_reminders(
    db: Session,
    today: date | None = None,
    sender=None
) -> int:
    """
    Надсилає email для товарів, дата покупки яких
    настала або вже минула.

    Повторне нагадування одному користувачу
    про один товар протягом того самого дня
    не надсилається.
    """

    if today is None:
        timezone_name = os.getenv(
            "REMINDER_TIMEZONE",
            "Europe/Kyiv"
        )

        today = datetime.now(
            ZoneInfo(timezone_name)
        ).date()

    if sender is None:
        sender = send_reminder_email

    items = (
        db.query(models.ShoppingItemModel)
        .filter(
            models.ShoppingItemModel.is_purchased.is_(False),
            models.ShoppingItemModel.planned_date.isnot(None)
        )
        .all()
    )

    sent_count = 0

    for item in items:

        planned_date = get_local_planned_date(
            item.planned_date
        )

        # Майбутні покупки поки не потребують листа.
        if planned_date > today:
            continue

        # Без email одержувача відправлення неможливе.
        if not item.created_by_email:
            continue

        # Не надсилаємо повторно протягом дня.
        if item.last_email_reminder_date == today:
            continue

        overdue = planned_date < today

        try:
            sender(
                recipient_email=item.created_by_email,
                item_name=item.name,
                quantity=item.quantity,
                planned_date=planned_date,
                overdue=overdue
            )

            # Фіксуємо дату тільки після успішної
            # передачі листа SMTP-серверу.
            item.last_email_reminder_date = today

            db.commit()

            sent_count += 1

            logger.info(
                "Reminder email sent for shopping item ID=%s",
                item.id
            )

        except Exception:
            db.rollback()

            logger.exception(
                "Failed to send reminder for shopping item ID=%s",
                item.id
            )

    return sent_count
