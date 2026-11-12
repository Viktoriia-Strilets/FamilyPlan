
import os

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

SESSION_SECRET_KEY = os.getenv(
    "SESSION_SECRET_KEY",
    "development-session-secret"
)

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@familyplan.com")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "SystemAdmin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "SuperSecretPassword123")
