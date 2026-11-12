
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import schemas, models
from app.models import UserModel
from app.core.dependencies import get_current_user
from app.services import family_service


router = APIRouter(tags=["Families"])


@router.post(
    "/families",
    response_model=schemas.FamilyResponse,
    status_code=201
)
def create_family(
    family: schemas.FamilyCreate,
    db: Session = Depends(get_db)
):
    return family_service.create_family(db, family.name)


@router.get("/families", response_model=list[schemas.FamilyResponse])
def get_families(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    if current_user.role == "admin":
        return db.query(models.FamilyModel).all()

    if not current_user.family_id:
        return []

    family = db.query(models.FamilyModel).filter(
        models.FamilyModel.id == current_user.family_id
    ).first()

    return [family] if family else []


@router.put(
    "/families/{family_id}",
    response_model=schemas.FamilyResponse
)
def update_family(
    family_id: int,
    family_update: schemas.FamilyCreate,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role != "admin" and (
        current_user.role != "head"
        or current_user.family_id != family_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Недостатньо прав для редагування цієї родини"
        )

    return family_service.update_family(
        db,
        family_id,
        family_update.name
    )


@router.delete("/families/{family_id}")
def delete_family(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if current_user.role != "admin" and (
        current_user.role != "head"
        or current_user.family_id != family_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Недостатньо прав для видалення цієї родини"
        )

    return family_service.delete_family(db, family_id)


@router.get(
    "/families/{family_id}/members",
    response_model=list[schemas.UserResponse]
)
def get_family_members(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    if (
        current_user.role != "admin"
        and current_user.family_id != family_id
    ):
        raise HTTPException(
            status_code=403,
            detail="Недостатньо прав для перегляду членів цієї родини"
        )

    return family_service.get_family_members(db, family_id)
