
from datetime import date, datetime, timedelta

from app import models
from app.services.reminder_service import process_due_reminders


def create_item(
    db,
    name,
    planned_date,
    email="user@test.com",
    is_purchased=False,
    last_reminder_date=None
):
    item = models.ShoppingItemModel(
        family_id=1,
        created_by="Test User",
        created_by_email=email,
        name=name,
        quantity=1,
        planned_date=datetime.combine(
            planned_date,
            datetime.min.time()
        ),
        is_purchased=is_purchased,
        last_email_reminder_date=last_reminder_date
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


def test_today_and_overdue_items_send_emails(db):
    today = date(2026, 11, 12)

    create_item(
        db,
        "Молоко",
        today
    )

    create_item(
        db,
        "Хліб",
        today - timedelta(days=2)
    )

    create_item(
        db,
        "Сік",
        today + timedelta(days=3)
    )

    sent_emails = []

    def fake_sender(**kwargs):
        sent_emails.append(kwargs)

    result = process_due_reminders(
        db,
        today=today,
        sender=fake_sender
    )

    assert result == 2
    assert len(sent_emails) == 2

    assert any(
        email["item_name"] == "Молоко"
        and email["overdue"] is False
        for email in sent_emails
    )

    assert any(
        email["item_name"] == "Хліб"
        and email["overdue"] is True
        for email in sent_emails
    )


def test_reminder_is_not_sent_twice_on_same_day(db):
    today = date(2026, 11, 12)

    create_item(
        db,
        "Молоко",
        today,
        last_reminder_date=today
    )

    sent_emails = []

    result = process_due_reminders(
        db,
        today=today,
        sender=lambda **kwargs: sent_emails.append(kwargs)
    )

    assert result == 0
    assert sent_emails == []


def test_reminder_is_sent_again_next_day_for_overdue_item(db):
    today = date(2026, 11, 12)

    create_item(
        db,
        "Хліб",
        today - timedelta(days=1),
        last_reminder_date=today - timedelta(days=1)
    )

    sent_emails = []

    result = process_due_reminders(
        db,
        today=today,
        sender=lambda **kwargs: sent_emails.append(kwargs)
    )

    assert result == 1
    assert len(sent_emails) == 1
    assert sent_emails[0]["overdue"] is True


def test_purchased_item_does_not_send_reminder(db):
    today = date(2026, 11, 12)

    create_item(
        db,
        "Молоко",
        today,
        is_purchased=True
    )

    sent_emails = []

    result = process_due_reminders(
        db,
        today=today,
        sender=lambda **kwargs: sent_emails.append(kwargs)
    )

    assert result == 0
    assert sent_emails == []


def test_item_without_email_does_not_send_reminder(db):
    today = date(2026, 11, 12)

    create_item(
        db,
        "Хліб",
        today,
        email=None
    )

    sent_emails = []

    result = process_due_reminders(
        db,
        today=today,
        sender=lambda **kwargs: sent_emails.append(kwargs)
    )

    assert result == 0
    assert sent_emails == []


def test_failed_email_does_not_mark_reminder_as_sent(db):
    today = date(2026, 11, 12)

    item = create_item(
        db,
        "Молоко",
        today
    )

    def failing_sender(**kwargs):
        raise RuntimeError("SMTP connection failed")

    result = process_due_reminders(
        db,
        today=today,
        sender=failing_sender
    )

    db.refresh(item)

    assert result == 0
    assert item.last_email_reminder_date is None
