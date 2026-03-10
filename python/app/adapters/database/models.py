from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.adapters.database.config import Base


class TimeDepositORM(Base):
    __tablename__ = "timeDeposits"

    id = Column(Integer, primary_key=True, index=True)
    plan_type = Column(String, nullable=False)
    days = Column(Integer, nullable=False)
    balance = Column(Float, nullable=False)

    # Relationship to withdrawals
    withdrawals = relationship("WithdrawalORM", back_populates="time_deposit", cascade="all, delete-orphan")


class WithdrawalORM(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, index=True)
    time_deposit_id = Column(Integer, ForeignKey("timeDeposits.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)

    # Foreign key to time deposits table
    time_deposit = relationship("TimeDepositORM", back_populates="withdrawals")
