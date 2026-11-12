
from fastapi import HTTPException


def check_family_head(current_user):
    if not current_user.family_id:
        raise HTTPException(
            status_code=400,
            detail="Користувач не належить до жодної родини"
        )

    if current_user.role != "head":
        raise HTTPException(
            status_code=403,
            detail="Лише голова родини може виконувати цю дію"
        )
