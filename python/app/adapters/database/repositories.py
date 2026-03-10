from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.models import TimeDeposit, Withdrawal
from app.domain.ports import TimeDepositRepository, WithdrawalRepository
from app.adapters.database.models import TimeDepositORM, WithdrawalORM


class PostgresTimeDepositRepository(TimeDepositRepository):
    """PostgreSQL implementation of TimeDepositRepository port"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, include_withdrawals: bool = True) -> List[TimeDeposit]:
        """Retrieve all time deposits with their withdrawals"""
        if include_withdrawals:
            result = await self.session.execute(
                select(TimeDepositORM).options(selectinload(TimeDepositORM.withdrawals))
            )
        else:
            result = await self.session.execute(
                select(TimeDepositORM)
            )
        orm_deposits = result.scalars().all()
        return [self._to_domain(orm_deposit, include_withdrawals) for orm_deposit in orm_deposits]

    async def get_by_id(self, deposit_id: int) -> Optional[TimeDeposit]:
        """Retrieve a time deposit by ID with its withdrawals"""
        result = await self.session.execute(
            select(TimeDepositORM)
            .options(selectinload(TimeDepositORM.withdrawals))
            .where(TimeDepositORM.id == deposit_id)
        )
        orm_deposit = result.scalar_one_or_none()
        return self._to_domain(orm_deposit) if orm_deposit else None

    async def save(self, deposit: TimeDeposit) -> TimeDeposit:
        """Create or update a time deposit"""
        if deposit.id:
            # Update existing - don't load withdrawals to avoid lazy load issues
            result = await self.session.execute(
                select(TimeDepositORM).where(TimeDepositORM.id == deposit.id)
            )
            orm_deposit = result.scalar_one_or_none()
            if orm_deposit:
                orm_deposit.plan_type = deposit.planType
                orm_deposit.days = deposit.days
                orm_deposit.balance = deposit.balance
                # Don't flush - let the commit happen at the route level
            else:
                raise ValueError(f"TimeDeposit with id {deposit.id} not found")
        else:
            # Create new
            orm_deposit = self._to_orm(deposit)
            self.session.add(orm_deposit)

        # Return domain model without withdrawals (they weren't modified anyway)
        return deposit

    async def delete(self, deposit_id: int) -> bool:
        """Delete a time deposit"""
        result = await self.session.execute(
            select(TimeDepositORM).where(TimeDepositORM.id == deposit_id)
        )
        orm_deposit = result.scalar_one_or_none()
        if orm_deposit:
            await self.session.delete(orm_deposit)
            await self.session.commit()
            return True
        return False

    @staticmethod
    def _to_domain(orm_deposit: TimeDepositORM, include_withdrawals: bool = True) -> TimeDeposit:
        """Convert ORM model to domain model"""
        withdrawals = []

        # Only include withdrawals if requested and they're available
        if include_withdrawals:
            try:
                # Try to access withdrawals - this will work if they're eagerly loaded
                withdrawals = [
                    Withdrawal(
                        id=w.id,
                        timeDepositId=w.time_deposit_id,
                        amount=w.amount,
                        date=w.date
                    )
                    for w in orm_deposit.withdrawals
                ]
            except:
                # If lazy loading fails, just return empty list
                withdrawals = []

        return TimeDeposit(
            id=orm_deposit.id,
            planType=orm_deposit.plan_type,
            days=orm_deposit.days,
            balance=orm_deposit.balance,
            withdrawals=withdrawals
        )

    @staticmethod
    def _to_orm(deposit: TimeDeposit) -> TimeDepositORM:
        """Convert domain model to ORM model"""
        return TimeDepositORM(
            id=deposit.id if deposit.id else None,
            plan_type=deposit.planType,
            days=deposit.days,
            balance=deposit.balance,
        )


class PostgresWithdrawalRepository(WithdrawalRepository):
    """PostgreSQL implementation of WithdrawalRepository port"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_time_deposit_id(self, time_deposit_id: int) -> List[Withdrawal]:
        """Retrieve all withdrawals for a time deposit"""
        result = await self.session.execute(
            select(WithdrawalORM).where(WithdrawalORM.time_deposit_id == time_deposit_id)
        )
        orm_withdrawals = result.scalars().all()
        return [self._to_domain(orm_withdrawal) for orm_withdrawal in orm_withdrawals]

    async def save(self, withdrawal: Withdrawal) -> Withdrawal:
        """Create a withdrawal"""
        orm_withdrawal = self._to_orm(withdrawal)
        self.session.add(orm_withdrawal)
        await self.session.commit()
        await self.session.refresh(orm_withdrawal)
        return self._to_domain(orm_withdrawal)

    @staticmethod
    def _to_domain(orm_withdrawal: WithdrawalORM) -> Withdrawal:
        """Convert ORM model to domain model"""
        return Withdrawal(
            id=orm_withdrawal.id,
            timeDepositId=orm_withdrawal.time_deposit_id,
            amount=orm_withdrawal.amount,
            date=orm_withdrawal.date,
        )

    @staticmethod
    def _to_orm(withdrawal: Withdrawal) -> WithdrawalORM:
        """Convert domain model to ORM model"""
        return WithdrawalORM(
            id=withdrawal.id if withdrawal.id else None,
            time_deposit_id=withdrawal.timeDepositId,
            amount=withdrawal.amount,
            date=withdrawal.date,
        )
