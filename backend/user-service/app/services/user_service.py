
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import UserModel, FamilyModel
from app.core.security import get_password_hash
from app.services.family_service import create_family

def register_user(db: Session, user_data):
    existing_user = (
        db.query(UserModel)
        .filter(UserModel.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Користувач із такою електронною поштою вже існує"
        )

    # Сценарій 1: створення нової родини.
    if user_data.create_family:
        if not user_data.family_name or not user_data.family_name.strip():
            raise HTTPException(
                status_code=400,
                detail="Вкажіть назву нової родини"
            )

        family = create_family(db, user_data.family_name.strip())
        role = "head"

    # Сценарій 2: приєднання за кодом запрошення.
    else:
        if not user_data.invite_code or not user_data.invite_code.strip():
            raise HTTPException(
                status_code=400,
                detail="Введіть код запрошення родини"
            )

        family = (
            db.query(FamilyModel)
            .filter(
                FamilyModel.invite_code
                == user_data.invite_code.strip().upper()
            )
            .first()
        )

        if not family:
            raise HTTPException(
                status_code=404,
                detail="Родину з таким кодом запрошення не знайдено"
            )

        # Якщо в родині ще немає голови,
        # перший зареєстрований користувач стає головою.
        existing_head = (
            db.query(UserModel)
            .filter(
                UserModel.family_id == family.id,
                UserModel.role == "head"
            )
            .first()
        )

        role = "head" if existing_head is None else "member"

    db_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        role=role,
        family_id=family.id
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception:
        db.rollback()
        raise

    return db_user


def get_users(db: Session, current_user: UserModel):
    if current_user.role == "admin":
        return db.query(UserModel).all()

    return (
        db.query(UserModel)
        .filter(UserModel.family_id == current_user.family_id)
        .all()
    )


def get_user_by_id(db: Session, user_id: int):
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

    return user


def update_user(db: Session, user: UserModel, user_update):
    if user_update.role is not None and user_update.role != user.role:
        if user_update.role not in ("head", "member", "admin"):
            raise HTTPException(
                status_code=400,
                detail="Некоректна роль користувача"
            )

        if user.role == "head" and user_update.role != "head" and user.family_id:
            other_heads = (
                db.query(UserModel)
                .filter(
                    UserModel.id != user.id,
                    UserModel.family_id == user.family_id,
                    UserModel.role == "head"
                )
                .count()
            )

            if other_heads == 0:
                raise HTTPException(
                    status_code=400,
                    detail="Неможливо забрати роль голови: у родині немає інших голів."
                )

        user.role = user_update.role

    if user_update.username is not None:
        user.username = user_update.username

    if user_update.email is not None:
        existing_email = (
            db.query(UserModel)
            .filter(
                UserModel.email == user_update.email,
                UserModel.id != user.id
            )
            .first()
        )

        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Користувач із такою поштою вже існує"
            )

        user.email = user_update.email

    db.commit()
    db.refresh(user)

    return user


def delete_user(db: Session, user: UserModel):
    family_id = user.family_id
    is_head = user.role == "head"

    db.delete(user)
    db.commit()

    if is_head and family_id:
        new_head = (
            db.query(UserModel)
            .filter(UserModel.family_id == family_id)
            .first()
        )

        if new_head:
            new_head.role = "head"
            db.commit()
        else:
            family = (
                db.query(FamilyModel)
                .filter(FamilyModel.id == family_id)
                .first()
            )

            if family:
                db.delete(family)
                db.commit()

    return {"message": "Користувача успішно видалено"}
