
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UserModel
from app.core.dependencies import get_current_user
from app.services import admin_service


router = APIRouter(
    prefix="/admin",
    tags=["Administration"]
)


def require_admin(current_user: UserModel):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Доступ заборонено. Тільки для адміністраторів."
        )


@router.get("/families")
def get_families_for_admin(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    require_admin(current_user)

    return admin_service.get_all_families_for_admin(db)


@router.delete("/families/{family_id}")
def delete_family_for_admin(
    family_id: int,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    require_admin(current_user)

    result = admin_service.delete_family_by_admin(
        db,
        family_id
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Родину не знайдено"
        )

    return result
