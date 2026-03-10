from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.services import TimeDepositService
from app.domain.models import TimeDeposit
from app.domain.ports import TimeDepositRepository
from app.adapters.database.config import get_db
from app.adapters.database.repositories import PostgresTimeDepositRepository

router = APIRouter()


# DTOs (Data Transfer Objects) for API
class WithdrawalResponse(BaseModel):
    id: int
    timeDepositId: int
    amount: float
    date: datetime

    model_config = {"from_attributes": True}


class TimeDepositResponse(BaseModel):
    id: int
    planType: str
    days: int
    balance: float
    withdrawals: List[WithdrawalResponse] = []

    model_config = {"from_attributes": True}


# Dependency injection
def get_repository(session: AsyncSession = Depends(get_db)) -> TimeDepositRepository:
    """Provide repository implementation"""
    return PostgresTimeDepositRepository(session)


def get_service(repository: TimeDepositRepository = Depends(get_repository)) -> TimeDepositService:
    """Provide service with injected repository"""
    return TimeDepositService(repository)


# Routes
@router.get("/", response_model=List[TimeDepositResponse])
async def get_deposits(service: TimeDepositService = Depends(get_service)):
    """List all time deposits with their withdrawals"""
    deposits = await service.get_time_deposits()

    return [
        TimeDepositResponse(
            id=deposit.id,
            planType=deposit.planType,
            days=deposit.days,
            balance=deposit.balance,
            withdrawals=[
                WithdrawalResponse(
                    id=w.id,
                    timeDepositId=w.timeDepositId,
                    amount=w.amount,
                    date=w.date
                )
                for w in deposit.withdrawals
            ]
        )
        for deposit in deposits
    ]


class UpdateResponse(BaseModel):
    message: str
    updated_count: int


@router.put("/balances", response_model=UpdateResponse)
async def update_deposit_balances(
    service: TimeDepositService = Depends(get_service),
    session: AsyncSession = Depends(get_db)
):
    """Update all time deposit balances with interest calculation"""
    count = await service.update_time_deposits()

    # Commit the transaction
    await session.commit()

    return UpdateResponse(
        message="Time deposit balances updated successfully",
        updated_count=count
    )
