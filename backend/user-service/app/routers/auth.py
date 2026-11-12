
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.models import UserModel
from app.core.security import (
    verify_password,
    create_access_token,
    get_password_hash
)
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.dependencies import get_current_user
from app.core.oauth import oauth
from app.services.user_service import register_user


router = APIRouter(tags=["Authentication"])


@router.post(
    "/users/register",
    response_model=schemas.UserResponse,
    status_code=201
)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return register_user(db, user)


@router.post("/users/login")
def login(
    credentials: schemas.UserLogin,
    db: Session = Depends(get_db)
):
    user = (
        db.query(UserModel)
        .filter(UserModel.email == credentials.email)
        .first()
    )

    if not user or not verify_password(
        credentials.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Неправильна пошта або пароль"
        )

    token = create_access_token(
        data={
            "sub": user.email,
            "username": user.username,
            "role": user.role,
            "family_id": user.family_id
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "family_id": user.family_id
    }


@router.get("/users/auth/google")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_auth_callback")

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


@router.get("/users/auth/google/callback")
async def google_auth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Помилка авторизації через Google"
        )

    user_info = token.get("userinfo")

    if not user_info:
        raise HTTPException(
            status_code=400,
            detail="Не вдалося отримати дані користувача від Google"
        )

    email = user_info.get("email")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Google не повернув електронну пошту"
        )

    user = (
        db.query(UserModel)
        .filter(UserModel.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=400,
            detail="Користувача з такою поштою не зареєстровано в жодній родині"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "username": user.username,
            "role": user.role,
            "family_id": user.family_id
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    return {
        "message": "Успішна авторизація через Google",
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "family_id": user.family_id
    }


@router.put("/users/me/password")
def change_password(
    data: schemas.PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if not verify_password(
        data.old_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=400,
            detail="Неправильний поточний пароль"
        )

    current_user.password_hash = get_password_hash(
        data.new_password
    )

    db.commit()

    return {"message": "Пароль успішно змінено"}
