
import logging
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine, SessionLocal
from app import models
from app.routers import items, recommendations, reminders
from app.services.reminder_service import process_due_reminders


logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shopping Service",
    version="2.0"
)

scheduler = None


def run_reminder_job():
    """
    Функція, яку APScheduler запускає автоматично.
    """

    db = SessionLocal()

    try:
        sent_count = process_due_reminders(db)

        logger.info(
            "Reminder job completed. Sent emails: %s",
            sent_count
        )

    except Exception:
        logger.exception(
            "Reminder scheduler job failed"
        )

    finally:
        db.close()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(items.router)
app.include_router(recommendations.router)
app.include_router(reminders.router)


@app.on_event("startup")
def start_reminder_scheduler():
    global scheduler
    Base.metadata.create_all(bind=engine)
    logger.info("Shopping Service database tables initialized")

    enabled = os.getenv(
        "ENABLE_EMAIL_REMINDERS",
        "true"
    ).lower() == "true"

    if not enabled:
        logger.info("Email reminder scheduler is disabled")
        return

    timezone_name = os.getenv(
        "REMINDER_TIMEZONE",
        "Europe/Kyiv"
    )

    hour = int(
        os.getenv("REMINDER_HOUR", "9")
    )

    minute = int(
        os.getenv("REMINDER_MINUTE", "0")
    )

    scheduler = BackgroundScheduler(
        timezone=timezone_name
    )

    scheduler.add_job(
        run_reminder_job,
        trigger="cron",
        hour=hour,
        minute=minute,
        id="shopping_email_reminders",
        replace_existing=True,
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

    logger.info(
        "Email reminder scheduler started: %02d:%02d (%s)",
        hour,
        minute,
        timezone_name
    )


@app.on_event("shutdown")
def stop_reminder_scheduler():
    global scheduler

    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)

        logger.info(
            "Email reminder scheduler stopped"
        )


@app.get("/")
def root():
    return {
        "message": "Shopping Service is running"
    }
