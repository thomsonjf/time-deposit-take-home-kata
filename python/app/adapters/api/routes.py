from typing import List
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
class TimeDepositResponse(BaseModel):
    id: int
    planType: str
    days: int
    balance: float

    class Config:
        from_attributes = True


# Dependency injection
def get_repository(session: AsyncSession = Depends(get_db)) -> TimeDepositRepository:
    """Provide repository implementation"""
    return PostgresTimeDepositRepository(session)


def get_service(repository: TimeDepositRepository = Depends(get_repository)) -> TimeDepositService:
    """Provide service with injected repository"""
    return TimeDepositService(repository)


# Routes
@router.get("/deposits", response_model=List[TimeDepositResponse])
async def get_deposits(service: TimeDepositService = Depends(get_service)):
    """Get all time deposits"""
    deposits = await service.get_time_deposits()
    return [TimeDepositResponse.model_validate(deposit) for deposit in deposits]


@router.put("/deposits/balances", response_model=List[TimeDepositResponse])
async def update_deposit_balances(service: TimeDepositService = Depends(get_service)):
    """Update all time deposit balances with interest calculation"""
    deposits = await service.update_time_deposits()
    return [TimeDepositResponse.model_validate(deposit) for deposit in deposits]
