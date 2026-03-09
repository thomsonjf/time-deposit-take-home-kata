from domain.models import TimeDeposit
from domain.models import Withdrawal

class TimeDepositService:
    # def __init__(self):
    
    def get_time_deposits():
        return [TimeDeposit(id=1, planType='student', days=4, balance=123.45)]

    def update_time_deposits():
        # Update time deposits
        
        return True
