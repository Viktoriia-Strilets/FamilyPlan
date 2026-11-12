
import os
import uuid

from datetime import datetime, timedelta
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.oauth import oauth
from app.core.security import (
    create_access_token,
    get_password_hash
)
from app.core.config import SECRET_KEY, ALGORITHM
from app.core.dependencies import get_current_user
from app.database import get_db
from app import models, schemas


router = APIRouter(prefix="/auth", tags=["OAuth"])

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
).rstrip("/")

def get_google_redirect_uri():
    return os.getenv("GOOGLE_REDIRECT_URI")


def create_temporary_token(data: dict, purpose: str, minutes: int = 10):
    payload = {
        **data,
        "purpose": purpose,
        "exp": datetime.utcnow() + timedelta(minutes=minutes)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def decode_temporary_token(token: str, purpose: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("purpose") != purpose:
            raise HTTPException(
                status_code=401,
                detail="Некоректний тип тимчасового токена"
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Токен недійсний або термін його дії закінчився"
        )


def make_frontend_redirect(**params):
    fragment = "&".join(
        f"{key}={quote(str(value), safe='')}"
        for key, value in params.items()
    )

    return RedirectResponse(
        url=f"{FRONTEND_URL}/oauth/callback#{fragment}"
    )


@router.get("/google/login")
async def google_login(request: Request):
    if not getattr(oauth, "google", None):
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured"
        )

    redirect_uri = get_google_redirect_uri()

    if not redirect_uri:
        raise HTTPException(
            status_code=503,
            detail="Google redirect URI is not configured"
        )

    request.session["oauth_action"] = "login"

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get("userinfo")

        if not user_info:
            raise HTTPException(
                status_code=401,
                detail="Не вдалося отримати дані Google"
            )

        google_id = user_info.get("sub")
        email = user_info.get("email")
        email_verified = user_info.get("email_verified", False)

        if not google_id or not email or not email_verified:
            raise HTTPException(
                status_code=401,
                detail="Google-акаунт не пройшов перевірку"
            )

        action = request.session.pop(
            "oauth_action",
            "login"
        )

        # -------------------------------------------------
        # 1. Прив'язування Google до існуючого акаунта
        # -------------------------------------------------

        if action == "link":
            user_id = request.session.pop(
                "oauth_link_user_id",
                None
            )

            if not user_id:
                raise HTTPException(
                    status_code=401,
                    detail="Сесія прив'язування Google втрачена"
                )

            user = (
                db.query(models.UserModel)
                .filter(models.UserModel.id == user_id)
                .first()
            )

            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="Користувача не знайдено"
                )

            linked_account = (
                db.query(models.OAuthAccountModel)
                .filter_by(
                    provider="google",
                    provider_user_id=google_id
                )
                .first()
            )

            if linked_account and linked_account.user_id != user.id:
                raise HTTPException(
                    status_code=409,
                    detail="Цей Google-акаунт уже прив'язаний до іншого користувача"
                )

            user_google_account = (
                db.query(models.OAuthAccountModel)
                .filter_by(
                    provider="google",
                    user_id=user.id
                )
                .first()
            )

            if user_google_account:
                if user_google_account.provider_user_id != google_id:
                    raise HTTPException(
                        status_code=409,
                        detail="До цього акаунта вже прив'язаний інший Google-акаунт"
                    )
            else:
                db.add(
                    models.OAuthAccountModel(
                        user_id=user.id,
                        provider="google",
                        provider_user_id=google_id,
                        email=email
                    )
                )

            db.commit()

            return make_frontend_redirect(
                google_linked="1"
            )

        # -------------------------------------------------
        # 2. Перевіряємо, чи Google уже прив'язаний
        # -------------------------------------------------

        oauth_account = (
            db.query(models.OAuthAccountModel)
            .filter_by(
                provider="google",
                provider_user_id=google_id
            )
            .first()
        )

        if oauth_account:
            user = oauth_account.user

            access_token = create_access_token({
                "sub": user.email,
                "username": user.username,
                "role": user.role,
                "family_id": user.family_id
            })

            return make_frontend_redirect(
                access_token=access_token
            )

        # -------------------------------------------------
        # 3. Google не прив'язаний, перевіряємо email
        # -------------------------------------------------

        existing_user = (
            db.query(models.UserModel)
            .filter(
                models.UserModel.email == email
            )
            .first()
        )

        if existing_user:
            return make_frontend_redirect(
                oauth_error="account_exists"
            )

        # -------------------------------------------------
        # 4. Новий користувач — лише тимчасовий токен
        # -------------------------------------------------

        registration_token = create_temporary_token(
            {
                "google_id": google_id,
                "email": email,
                "username": (
                    user_info.get("name")
                    or email.split("@")[0]
                )
            },
            purpose="google_registration",
            minutes=10
        )

        return make_frontend_redirect(
            google_registration_token=registration_token
        )

    except HTTPException:
        db.rollback()
        raise

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=401,
            detail="Помилка авторизації через Google"
        ) from exc


# -----------------------------------------------------
# 5. Завершення Google-реєстрації
# -----------------------------------------------------

@router.post("/google/register")
def complete_google_registration(
    data: schemas.GoogleRegistrationComplete,
    db: Session = Depends(get_db)
):
    payload = decode_temporary_token(
        data.registration_token,
        "google_registration"
    )

    google_id = payload.get("google_id")
    email = payload.get("email")

    if not google_id or not email:
        raise HTTPException(
            status_code=400,
            detail="Некоректні дані Google-реєстрації"
        )

    if db.query(models.UserModel).filter_by(email=email).first():
        raise HTTPException(
            status_code=409,
            detail="Користувач із такою поштою вже існує"
        )

    if db.query(models.OAuthAccountModel).filter_by(
        provider="google",
        provider_user_id=google_id
    ).first():
        raise HTTPException(
            status_code=409,
            detail="Цей Google-акаунт уже зареєстрований"
        )

    if data.create_family:
        family_name = (data.family_name or "").strip()

        if not family_name:
            raise HTTPException(
                status_code=400,
                detail="Вкажіть назву нової родини"
            )

        if db.query(models.FamilyModel).filter_by(
            name=family_name
        ).first():
            raise HTTPException(
                status_code=400,
                detail="Родина з такою назвою вже існує"
            )

        family = models.FamilyModel(
            name=family_name,
            invite_code=str(uuid.uuid4())[:8].upper()
        )

        role = "head"

    else:
        invite_code = (data.invite_code or "").strip().upper()

        if not invite_code:
            raise HTTPException(
                status_code=400,
                detail="Введіть код запрошення родини"
            )

        family = (
            db.query(models.FamilyModel)
            .filter_by(invite_code=invite_code)
            .first()
        )

        if not family:
            raise HTTPException(
                status_code=404,
                detail="Родину з таким кодом запрошення не знайдено"
            )

        role = "member"

    username = (
        data.username or payload.get("username") or email.split("@")[0]
    ).strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Вкажіть ім'я користувача"
        )

    try:
        if data.create_family:
            db.add(family)
            db.flush()

        user = models.UserModel(
            username=username,
            email=email,
            password_hash=get_password_hash(data.password),
            role=role,
            family_id=family.id
        )

        db.add(user)
        db.flush()

        oauth_account = models.OAuthAccountModel(
            user_id=user.id,
            provider="google",
            provider_user_id=google_id,
            email=email
        )

        db.add(oauth_account)
        db.commit()
        db.refresh(user)

    except Exception:
        db.rollback()
        raise

    access_token = create_access_token({
        "sub": user.email,
        "username": user.username,
        "role": user.role,
        "family_id": user.family_id
    })

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "family_id": user.family_id
    }


# -----------------------------------------------------
# 6. Створення короткоживучого токена для прив'язування
# -----------------------------------------------------

@router.post("/google/link-token")
def create_google_link_token(
    current_user: models.UserModel = Depends(get_current_user)
):
    link_token = create_temporary_token(
        {"user_id": current_user.id},
        purpose="google_link",
        minutes=2
    )

    return {"link_token": link_token}


@router.get("/google/link")
async def start_google_link(
    request: Request,
    link_token: str,
    db: Session = Depends(get_db)
):
    payload = decode_temporary_token(
        link_token,
        "google_link"
    )

    user_id = payload.get("user_id")

    user = (
        db.query(models.UserModel)
        .filter(models.UserModel.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Користувача не знайдено"
        )

    redirect_uri = get_google_redirect_uri()

    if not redirect_uri:
        raise HTTPException(
            status_code=503,
            detail="Google redirect URI is not configured"
        )

    request.session["oauth_action"] = "link"
    request.session["oauth_link_user_id"] = user.id

    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )
