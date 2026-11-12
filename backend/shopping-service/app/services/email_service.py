
import os
import ssl
import smtplib

from datetime import date
from email.message import EmailMessage


def send_reminder_email(
    recipient_email: str,
    item_name: str,
    quantity: int,
    planned_date: date,
    overdue: bool
):
    """
    Надсилає email-нагадування про заплановану
    або прострочену покупку.
    """

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "2525"))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")

    from_email = (
        os.getenv("SMTP_FROM_EMAIL")
        or smtp_username
    )

    if not all([
        smtp_host,
        smtp_username,
        smtp_password,
        from_email,
        recipient_email
    ]):
        raise RuntimeError(
            "Не налаштовані SMTP-параметри"
        )

    if overdue:
        subject = (
            f"FamilyPlan: прострочена покупка — {item_name}"
        )

        status_text = (
            "Термін покупки цього товару вже минув."
        )
    else:
        subject = (
            f"FamilyPlan: час купити — {item_name}"
        )

        status_text = (
            "Сьогодні заплановано придбати цей товар."
        )

    message = EmailMessage()

    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = recipient_email

    message.set_content(
        f"""
Вітаємо!

FamilyPlan нагадує про покупку.

Товар: {item_name}
Кількість: {quantity}
Запланована дата: {planned_date.strftime("%d.%m.%Y")}

{status_text}

Перейдіть до FamilyPlan, щоб переглянути список покупок.

Це автоматичне повідомлення.
"""
    )

    context = ssl.create_default_context()

    with smtplib.SMTP(
        smtp_host,
        smtp_port,
        timeout=20
    ) as server:

        server.ehlo()

        server.starttls(context=context)

        server.ehlo()

        server.login(
            smtp_username,
            smtp_password
        )

        server.send_message(message)
