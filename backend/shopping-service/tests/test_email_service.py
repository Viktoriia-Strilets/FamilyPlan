
from datetime import date
from email import message_from_bytes

from app.services.email_service import send_reminder_email


class FakeSMTP:
    def __init__(self, host, port, timeout):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.started_tls = False
        self.logged_in = False
        self.sent_message = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def ehlo(self):
        pass

    def starttls(self, context=None):
        self.started_tls = True

    def login(self, username, password):
        self.logged_in = True

    def send_message(self, message):
        self.sent_message = message


def test_send_reminder_email(monkeypatch):
    import smtplib

    fake_smtp = FakeSMTP(
        "sandbox.smtp.mailtrap.io",
        2525,
        20
    )

    def fake_smtp_factory(host, port, timeout):
        return fake_smtp

    monkeypatch.setattr(
        smtplib,
        "SMTP",
        fake_smtp_factory
    )

    monkeypatch.setenv(
        "SMTP_HOST",
        "sandbox.smtp.mailtrap.io"
    )
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USERNAME", "test_user")
    monkeypatch.setenv("SMTP_PASSWORD", "test_password")
    monkeypatch.setenv(
        "SMTP_FROM_EMAIL",
        "familyplan@example.com"
    )

    send_reminder_email(
        recipient_email="recipient@example.com",
        item_name="Молоко",
        quantity=2,
        planned_date=date(2026, 11, 12),
        overdue=False
    )

    assert fake_smtp.started_tls is True
    assert fake_smtp.logged_in is True

    message = fake_smtp.sent_message

    assert message is not None
    assert message["To"] == "recipient@example.com"
    assert "Молоко" in message["Subject"]
    assert "Молоко" in message.get_content()
    assert "12.11.2026" in message.get_content()
