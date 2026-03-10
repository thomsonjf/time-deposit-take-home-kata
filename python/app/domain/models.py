from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class TimeDeposit:
    id: int
    planType: str
    days: int
    balance: float
    withdrawals: List['Withdrawal'] = field(default_factory=list)

    def __init__(self, id, planType, balance, days, withdrawals=None):
        self.id = id
        self.planType = planType
        self.balance = balance
        self.days = days
        self.withdrawals = withdrawals if withdrawals is not None else []

@dataclass
class Withdrawal:
    id: Optional[int]
    timeDepositId: int
    amount: float
    date: datetime

