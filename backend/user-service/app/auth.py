import os
from datetime import datetime, timedelta, timezone

from jose import jwt

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY не заданий у змінних середовища")

ALGORITHM = os.getenv("ALGORITHM", "HS256")


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
) -> str:
    """
    Створює JWT access token.

    data — інформація, яка буде записана в токен.
    expires_delta — термін дії токена.
    """

    to_encode = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(minutes=30)

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt