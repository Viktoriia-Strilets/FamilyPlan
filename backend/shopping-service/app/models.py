
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    Date,
    Numeric,
    func
)

from app.database import Base


class ShoppingItemModel(Base):
    __tablename__ = "shopping_items"

    id = Column(Integer, primary_key=True, index=True)

    # Прив'язка товару до родини
    family_id = Column(Integer, nullable=False, index=True)
    source_expense_id = Column(
        Integer,
        nullable=True,
        unique=True,
        index=True
    )
    created_by = Column(String, nullable=False)

    # Email користувача, який створив товар.
    created_by_email = Column(
        String,
        nullable=True
    )

    # Інформація про товар
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    category = Column(String, nullable=True)

    # Ціни
    estimated_price = Column(Numeric(12, 2), nullable=True)
    actual_price = Column(Numeric(12, 2), nullable=True)

    # Запланована дата покупки
    planned_date = Column(DateTime(timezone=True), nullable=True)

    # Статус покупки
    is_purchased = Column(Boolean, default=False, nullable=False)
    purchased_at = Column(DateTime(timezone=True), nullable=True)

    # Дата останнього успішного email-нагадування.
    last_email_reminder_date = Column(
        Date,
        nullable=True
    )

    # Дати створення та оновлення
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

