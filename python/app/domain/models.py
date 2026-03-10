from dataclasses import dataclass
from datetime import datetime

@dataclass
class TimeDeposit:
    id: int
    planType: str
    days: int
    balance: float
    
    def __init__(self, id, planType, balance, days):
        self.id = id
        self.planType = planType
        self.balance = balance
        self.days = days

@dataclass
class Withdrawal:
    id: int
    timeDepositId: int
    amount: float
    date: datetime

