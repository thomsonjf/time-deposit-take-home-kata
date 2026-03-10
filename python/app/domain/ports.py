from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.models import TimeDeposit, Withdrawal

class TimeDepositRepository(ABC):
    """Port for time deposit persistence operations"""

    @abstractmethod
    async def get_all(self) -> List[TimeDeposit]:
        """Retrieve all time deposits"""
        pass

    @abstractmethod
    async def get_by_id(self, deposit_id: int) -> Optional[TimeDeposit]:
        """Retrieve a time deposit by ID"""
        pass

    @abstractmethod
    async def save(self, deposit: TimeDeposit) -> TimeDeposit:
        """Create or update a time deposit"""
        pass

    @abstractmethod
    async def delete(self, deposit_id: int) -> bool:
        """Delete a time deposit"""
        pass


class WithdrawalRepository(ABC):
    """Port for withdrawal persistence operations"""

    @abstractmethod
    async def get_by_time_deposit_id(self, time_deposit_id: int) -> List[Withdrawal]:
        """Retrieve all withdrawals for a time deposit"""
        pass

    @abstractmethod
    async def save(self, withdrawal: Withdrawal) -> Withdrawal:
        """Create a withdrawal"""
        pass
