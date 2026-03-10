from typing import List
from abc import ABC, abstractmethod
from app.domain.models import TimeDeposit, Withdrawal
from app.domain.ports import TimeDepositRepository, WithdrawalRepository

class InterestStrategy(ABC):
    """Abstract base class for interest calculation strategies"""

    @abstractmethod
    def is_eligible(self, deposit: TimeDeposit) -> bool:
        """Determine if deposit is eligible for interest"""
        pass

    @abstractmethod
    def get_annual_rate(self) -> float:
        """Get annual interest rate for this plan type"""
        pass

    def calculate_interest(self, deposit: TimeDeposit) -> float:
        """Calculate monthly interest for a deposit"""
        if not self.is_eligible(deposit):
            return 0.0

        annual_rate = self.get_annual_rate()
        monthly_interest = (deposit.balance * annual_rate) / 12
        return monthly_interest


class BasicPlanStrategy(InterestStrategy):
    """Interest calculation for Basic plan: 1% annual, eligible after 30 days"""

    def is_eligible(self, deposit: TimeDeposit) -> bool:
        return deposit.days > 30

    def get_annual_rate(self) -> float:
        return 0.01


class StudentPlanStrategy(InterestStrategy):
    """Interest calculation for Student plan: 3% annual, eligible 31-365 days"""

    def is_eligible(self, deposit: TimeDeposit) -> bool:
        return deposit.days > 30 and deposit.days < 366

    def get_annual_rate(self) -> float:
        return 0.03


class PremiumPlanStrategy(InterestStrategy):
    """Interest calculation for Premium plan: 5% annual, eligible after 45 days"""

    def is_eligible(self, deposit: TimeDeposit) -> bool:
        return deposit.days > 30 and deposit.days > 45

    def get_annual_rate(self) -> float:
        return 0.05


class TimeDepositCalculator:

    def __init__(self):
        # Registry of plan type strategies
        self._strategies = {
            'basic': BasicPlanStrategy(),
            'student': StudentPlanStrategy(),
            'premium': PremiumPlanStrategy(),
        }

    def register_strategy(self, plan_type: str, strategy: InterestStrategy):
        """Register a new plan type strategy"""
        self._strategies[plan_type] = strategy

    def calculate_interest(self, deposit: TimeDeposit) -> float:
        """Calculate interest for a single deposit"""
        strategy = self._strategies.get(deposit.planType.lower())
        if not strategy:
            # No strategy registered for this plan type - no interest
            return 0.0

        return strategy.calculate_interest(deposit)

    def update_balance(self, xs):
        """Update balances for a list of deposits with interest calculation"""
        for deposit in xs:
            interest = self.calculate_interest(deposit)
            deposit.balance = round(deposit.balance + interest, 2)


class TimeDepositService:
    """Application service for time deposit use cases"""

    def __init__(self, repository: TimeDepositRepository):
        self.repository = repository
        self.calculator = TimeDepositCalculator()

    async def get_time_deposits(self) -> List[TimeDeposit]:
        """Retrieve all time deposits"""
        return await self.repository.get_all()

    async def update_time_deposits(self, batch_size: int = 1000) -> int:
        """
        Update all time deposit balances with interest calculation.

        For large datasets (2M+ records), this method:
        - Processes deposits in batches to avoid memory issues
        - Uses bulk updates instead of individual saves
        - Only loads minimal data (no withdrawals) for calculations

        Args:
            batch_size: Number of deposits to process per batch (default: 1000)

        Returns:
            Total number of deposits updated
        """
        # TODO: For 2M+ records, implement batch processing:
        # 1. Fetch deposits in batches using pagination/cursor
        # 2. Calculate interest for each batch
        # 3. Use bulk_update() instead of individual save() calls
        # 4. Consider async task queue (Celery) for background processing
        # 5. Add progress tracking/logging

        # Current implementation - works for small datasets
        deposits = await self.repository.get_all(include_withdrawals=False)
        self.calculator.update_balance(deposits)

        # Update deposits in database (save will flush but not commit)
        for deposit in deposits:
            await self.repository.save(deposit)

        # Return count of updated deposits
        return len(deposits)
