"""Database seeding utilities for development and testing"""
from datetime import datetime
from typing import List

from app.domain.models import TimeDeposit, Withdrawal


def get_sample_deposits() -> List[TimeDeposit]:
    """Get sample time deposit data for seeding"""
    return [
        TimeDeposit(
            id=None,
            planType="student",
            days=60,
            balance=1000.0
        ),
        TimeDeposit(
            id=None,
            planType="student",
            days=180,
            balance=5000.0
        ),
        TimeDeposit(
            id=None,
            planType="premium",
            days=90,
            balance=10000.0
        ),
        TimeDeposit(
            id=None,
            planType="premium",
            days=25,  # Won't earn interest (< 45 days)
            balance=3000.0
        ),
        TimeDeposit(
            id=None,
            planType="basic",
            days=45,
            balance=2000.0
        ),
        TimeDeposit(
            id=None,
            planType="basic",
            days=20,  # Won't earn interest (< 30 days)
            balance=1500.0
        ),
    ]


def get_sample_withdrawals() -> List[Withdrawal]:
    """Get sample withdrawal data (optional - for future use)"""
    return [
        Withdrawal(
            id=None,
            timeDepositId=1,
            amount=100.0,
            date=datetime(2025, 1, 15)
        ),
        Withdrawal(
            id=None,
            timeDepositId=2,
            amount=500.0,
            date=datetime(2025, 2, 10)
        ),
    ]

async def seed_database(deposit_repository, withdrawal_repository=None):
    """Seed the database with sample data"""
    from app.adapters.database.models import TimeDepositORM, WithdrawalORM

    deposits_data = get_sample_deposits()

    # Add deposits directly to session
    for deposit_data in deposits_data:
        orm_deposit = TimeDepositORM(
            plan_type=deposit_data.planType,
            days=deposit_data.days,
            balance=deposit_data.balance
        )
        deposit_repository.session.add(orm_deposit)

    # Flush to get IDs
    await deposit_repository.session.flush()
    await deposit_repository.session.commit()

    # Seed withdrawals if withdrawal repository is provided
    if withdrawal_repository:
        withdrawals = get_sample_withdrawals()
        for withdrawal in withdrawals:
            orm_withdrawal = WithdrawalORM(
                time_deposit_id=withdrawal.timeDepositId,
                amount=withdrawal.amount,
                date=withdrawal.date
            )
            withdrawal_repository.session.add(orm_withdrawal)

        await withdrawal_repository.session.flush()
        await withdrawal_repository.session.commit()

    # Return created deposits
    return deposits_data
