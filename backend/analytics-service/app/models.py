from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint

from app.database import Base


class ExpenseReportModel(Base):
    __tablename__ = "expense_reports"

    id = Column(Integer, primary_key=True, index=True)

    family_id = Column(Integer, nullable=False, index=True)

    period = Column(String(7), nullable=False)
    total_spent = Column(Float, nullable=False, default=0.0)
    recommendations_text = Column(String, nullable=True)


class CategoryStatisticsModel(Base):
    __tablename__ = "category_statistics"

    id = Column(Integer, primary_key=True, index=True)

    family_id = Column(Integer, nullable=False, index=True)

    category = Column(String, nullable=False, index=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    period = Column(String(7), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "family_id",
            "category",
            "period",
            name="uq_family_category_period"
        ),
    )