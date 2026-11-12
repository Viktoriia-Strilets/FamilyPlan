
from sqlalchemy.orm import Session

from app.models import UserModel, OAuthAccountModel


def get_user_by_oauth_identity(
    db: Session,
    provider: str,
    provider_user_id: str
) -> UserModel | None:
    """
    Знаходить користувача за назвою OAuth-провайдера
    та його унікальним ідентифікатором.
    """

    if not provider or not provider_user_id:
        return None

    oauth_account = (
        db.query(OAuthAccountModel)
        .filter(
            OAuthAccountModel.provider == provider,
            OAuthAccountModel.provider_user_id == provider_user_id
        )
        .first()
    )

    if oauth_account is None:
        return None

    return oauth_account.user


def link_oauth_account(
    db: Session,
    user_id: int,
    provider: str,
    provider_user_id: str,
    email: str | None = None
) -> OAuthAccountModel:
    """
    Прив'язує зовнішній OAuth-акаунт до існуючого користувача.

    Не дозволяє:
    - прив'язувати акаунт до неіснуючого користувача;
    - повторно прив'язувати той самий зовнішній акаунт;
    - прив'язувати один зовнішній акаунт до різних користувачів.

    Виконує flush, але не commit: транзакцією керує викликач.
    """

    if not provider or not provider_user_id:
        raise ValueError("Провайдер та зовнішній ID обов'язкові")

    user = db.query(UserModel).filter(
        UserModel.id == user_id
    ).first()

    if user is None:
        raise ValueError("Користувача не знайдено")

    existing_account = (
        db.query(OAuthAccountModel)
        .filter(
            OAuthAccountModel.provider == provider,
            OAuthAccountModel.provider_user_id == provider_user_id
        )
        .first()
    )

    if existing_account is not None:
        if existing_account.user_id == user_id:
            raise ValueError("OAuth-акаунт вже прив'язаний до цього користувача")

        raise ValueError("OAuth-акаунт вже прив'язаний до іншого користувача")

    oauth_account = OAuthAccountModel(
        user_id=user_id,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email
    )

    db.add(oauth_account)
    db.flush()

    return oauth_account
