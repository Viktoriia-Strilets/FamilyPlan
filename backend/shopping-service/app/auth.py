
import os

from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials
)


SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY не заданий у змінних середовища")

ALGORITHM = os.getenv("ALGORITHM", "HS256")

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")
        username = payload.get("username")
        family_id = payload.get("family_id")
        role = payload.get("role")

        if not email or family_id is None:
            raise HTTPException(
                status_code=401,
                detail="Некоректний токен авторизації"
            )

        try:
            family_id = int(family_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=401,
                detail="Некоректний токен авторизації"
            )

        return {
            "email": email,
            "username": username,
            "family_id": family_id,
            "role": role
        }

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Недійсний або прострочений токен"
        )
