
import os

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app import models


SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY не заданий у змінних середовища")


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="http://localhost:8001/users/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неможливо валідувати облікові дані",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")
        role = payload.get("role")
        family_id = payload.get("family_id")
        username = payload.get("username")

        if not email or not role:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    user = db.query(models.UserModel).filter(
        models.UserModel.email == email
    ).first()

    if not user:
        user = models.UserModel(
            email=email,
            username=username or email.split("@")[0],
            role=role,
            family_id=family_id
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    else:
        # Оновлюємо кешовані дані з актуального JWT.
        user.username = username or user.username
        user.role = role
        user.family_id = family_id

        db.commit()
        db.refresh(user)

    return user
