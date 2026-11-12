
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import FamilyModel, UserModel


def create_family(db: Session, name: str):
    existing = (
        db.query(FamilyModel)
        .filter(FamilyModel.name == name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Родина з такою назвою вже існує"
        )

    family = FamilyModel(
        name=name,
        invite_code=str(uuid.uuid4())[:8].upper()
    )

    db.add(family)
    db.commit()
    db.refresh(family)

    return family


def get_all_families(db: Session):
    return db.query(FamilyModel).all()


def get_family_by_id(db: Session, family_id: int):
    family = (
        db.query(FamilyModel)
        .filter(FamilyModel.id == family_id)
        .first()
    )

    if not family:
        raise HTTPException(
            status_code=404,
            detail="Родину не знайдено"
        )

    return family


def update_family(db: Session, family_id: int, name: str):
    family = get_family_by_id(db, family_id)

    family.name = name

    db.commit()
    db.refresh(family)

    return family


def delete_family(db: Session, family_id: int):
    family = get_family_by_id(db, family_id)

    db.delete(family)
    db.commit()

    return {"message": "Родину успішно видалено"}


def get_family_members(db: Session, family_id: int):
    return (
        db.query(UserModel)
        .filter(UserModel.family_id == family_id)
        .all()
    )
