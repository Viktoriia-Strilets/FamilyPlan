
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas
from app.models import UserModel, OAuthAccountModel
from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.services import user_service


router = APIRouter(tags=["Users"])


@router.get(
    "/users",
    response_model=list[schemas.UserResponse]
)
def get_users(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    return user_service.get_users(db, current_user)


@router.get(
    "/users/me",
    response_model=schemas.UserResponse
)
def read_users_me(
    current_user: UserModel = Depends(get_current_user)
):
    invite_code = (
        current_user.family.invite_code
        if current_user.family
        else None
    )

    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "family_id": current_user.family_id,
        "family_invite_code": invite_code
    }


@router.put(
    "/users/{user_id}",
    response_model=schemas.UserResponse
)
def update_user_profile(
    user_id: int,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    user = user_service.get_user_by_id(db, user_id)

    is_self = current_user.id == user_id

    is_head_of_family = (
        current_user.role == "head"
        and current_user.family_id == user.family_id
    )

    if not is_self and not is_head_of_family:
        raise HTTPException(
            status_code=403,
            detail="Недостатньо прав для редагування"
        )

    # Звичайний користувач не може призначити собі
    # адміністративну роль.
    if user_update.role is not None:
        if current_user.role != "head":
            raise HTTPException(
                status_code=403,
                detail="Змінювати ролі може тільки голова родини"
            )

        if user_update.role == "admin":
            raise HTTPException(
                status_code=403,
                detail="Призначення адміністратора заборонено"
            )

    user = user_service.update_user(db, user, user_update)

    new_token = create_access_token(
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
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "family_id": user.family_id,
        "access_token": new_token
    }



@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    user = (
        db.query(UserModel)
        .filter(UserModel.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Користувача не знайдено"
        )

    is_admin = current_user.role == "admin"
    is_self = current_user.id == user_id

    is_head_of_same_family = (
        current_user.role == "head"
        and current_user.family_id is not None
        and current_user.family_id == user.family_id
    )

    if not (
        is_admin
        or is_self
        or is_head_of_same_family
    ):
        raise HTTPException(
            status_code=403,
            detail="Недостатньо прав для видалення цього користувача"
        )

    # Голова не може видалити іншого голову.
    # Адміністратор може.
    if (
        not is_admin
        and is_head_of_same_family
        and not is_self
        and user.role == "head"
    ):
        raise HTTPException(
            status_code=403,
            detail="Не можна видалити іншого голову родини"
        )

    try:
        # Видаляємо прив'язки OAuth.
        db.query(OAuthAccountModel).filter(
            OAuthAccountModel.user_id == user.id
        ).delete(synchronize_session=False)

        # Викликаємо сервіс, який також призначає нового голову,
        # якщо видаляється попередній.
        return user_service.delete_user(db, user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Не вдалося видалити акаунт"
        )
