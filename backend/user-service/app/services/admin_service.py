
from datetime import datetime, timedelta

from app.models import FamilyModel, UserModel


def get_all_families_for_admin(db):
    families = db.query(FamilyModel).all()

    six_months_ago = datetime.utcnow() - timedelta(days=180)

    result = []

    for family in families:
        last_activity = (
            family.last_activity_at or family.created_at
        )

        is_inactive = last_activity < six_months_ago

        heads = (
            db.query(UserModel)
            .filter(
                UserModel.family_id == family.id,
                UserModel.role == "head"
            )
            .all()
        )

        head_emails = [head.email for head in heads]

        result.append({
            "id": family.id,
            "name": family.name,
            "members_count": len(family.users),
            "head_emails": head_emails,
            "head_email": (
                head_emails[0]
                if head_emails
                else "Немає голови родини"
            ),
            "last_activity_at": last_activity,
            "is_inactive": is_inactive,
            "can_be_deleted": is_inactive
        })

    return result


def delete_family_by_admin(db, family_id: int):
    family = (
        db.query(FamilyModel)
        .filter(FamilyModel.id == family_id)
        .first()
    )

    if not family:
        return None

    family_name = family.name

    db.delete(family)
    db.commit()

    return {
        "message": (
            f"Родину '{family_name}' та всіх її учасників "
            "успішно видалено адміністратором."
        )
    }
