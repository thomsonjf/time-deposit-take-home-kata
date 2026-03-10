from typing import List
from app.domain.models import TimeDeposit, Withdrawal
from app.domain.ports import TimeDepositRepository, WithdrawalRepository

class TimeDepositService:
    """Application service for time deposit use cases"""

    def __init__(self, repository: TimeDepositRepository):
        self.repository = repository
        self.calculator = TimeDepositCalculator()

    async def get_time_deposits(self) -> List[TimeDeposit]:
        """Retrieve all time deposits"""
        return await self.repository.get_all()

    async def update_time_deposits(self) -> List[TimeDeposit]:
        """Update all time deposit balances with interest calculation"""
        deposits = await self.repository.get_all()
        self.calculator.update_balance(deposits)

        # Save updated deposits back to the database
        updated_deposits = []
        for deposit in deposits:
            updated = await self.repository.save(deposit)
            updated_deposits.append(updated)

        return updated_deposits


class TimeDepositCalculator:

    def update_balance(self,xs):
        for td in xs:
            interest = 0
            if td.days > 30:
                if td.planType == 'student':
                    if td.days < 366:
                        interest += (td.balance * 0.03)/12
                elif td.planType == 'premium':
                    if td.days > 45:
                        interest += (td.balance * 0.05)/12
                elif td.planType == 'basic':
                    interest += (td.balance * 0.01) / 12
            td.balance = round(td.balance + ((interest * 100) / 100), 2)
