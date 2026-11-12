
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class FamilyModel(Base):
    __tablename__ = "families"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    invite_code = Column(String, unique=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    users = relationship(
        "UserModel",
        back_populates="family",
        cascade="all, delete-orphan"
    )


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="member")

    family_id = Column(
        Integer,
        ForeignKey("families.id", ondelete="CASCADE"),
        nullable=True
    )

    family = relationship(
        "FamilyModel",
        back_populates="users"
    )
    @property
    def has_password(self):
        return bool(self.password_hash)

class OAuthAccountModel(Base):
    __tablename__ = "oauth_accounts"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    

    provider = Column(String, nullable=False)
    provider_user_id = Column(String, nullable=False)
    email = Column(String, nullable=True)
    user = relationship("UserModel", backref="oauth_accounts")


    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_oauth_provider_user"
        ),
    )