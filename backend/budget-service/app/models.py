
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class UserModel(Base):
    __tablename__ = "users_cache"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String)
    role = Column(String, default="member")
    family_id = Column(Integer, nullable=True)


class FamilyBudgetModel(Base):
    __tablename__ = "family_budgets"

    id = Column(Integer, primary_key=True, index=True)
    family_id = Column(Integer, index=True, nullable=False)
    total_planned_budget = Column(Float, default=0.0, nullable=False)
    currency = Column(String, default="UAH")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    expenses = relationship(
        "ExpenseModel",
        back_populates="budget",
        cascade="all, delete-orphan"
    )


class ExpenseModel(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(
        Integer,
        ForeignKey("family_budgets.id"),
        nullable=False
    )
    user_id = Column(Integer, nullable=False)
    username = Column(String, nullable=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, default="Загальні")
    is_planned = Column(Integer, default=0)
    date = Column(DateTime, default=datetime.utcnow)

    # ID покупки з Shopping Service.
    # Використовується для захисту від дублювання витрат.
    source_purchase_id = Column(
        Integer,
        nullable=True,
        unique=True,
        index=True
    )

    budget = relationship(
        "FamilyBudgetModel",
        back_populates="expenses"
    )