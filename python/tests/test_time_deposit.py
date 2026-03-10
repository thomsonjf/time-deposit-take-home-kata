from app.domain.models import TimeDeposit
from app.application.services import TimeDepositCalculator
import unittest

class TestTimeDepositCalculator(unittest.TestCase):

    def test_update_balance_student_eligible(self):
        """Test student plan with eligible days (> 30 and < 366) earns 3% interest"""
        deposits = [
            TimeDeposit(id=1, planType='student', balance=1000.0, days=60),
            TimeDeposit(id=2, planType='student', balance=5000.0, days=365),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # Student: 3% annual = (balance * 0.03) / 12 monthly
        self.assertEqual(deposits[0].balance, 1002.5)  # 1000 + (1000 * 0.03 / 12)
        self.assertEqual(deposits[1].balance, 5012.5)  # 5000 + (5000 * 0.03 / 12)

    def test_update_balance_student_not_eligible_too_few_days(self):
        """Test student plan with <= 30 days earns no interest"""
        deposits = [
            TimeDeposit(id=1, planType='student', balance=1000.0, days=30),
            TimeDeposit(id=2, planType='student', balance=2000.0, days=15),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # No interest applied
        self.assertEqual(deposits[0].balance, 1000.0)
        self.assertEqual(deposits[1].balance, 2000.0)

    def test_update_balance_student_not_eligible_too_many_days(self):
        """Test student plan with >= 366 days earns no interest"""
        deposits = [
            TimeDeposit(id=1, planType='student', balance=1000.0, days=366),
            TimeDeposit(id=2, planType='student', balance=2000.0, days=400),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # No interest applied
        self.assertEqual(deposits[0].balance, 1000.0)
        self.assertEqual(deposits[1].balance, 2000.0)

    def test_update_balance_premium_eligible(self):
        """Test premium plan with > 45 days earns 5% interest"""
        deposits = [
            TimeDeposit(id=1, planType='premium', balance=10000.0, days=46),
            TimeDeposit(id=2, planType='premium', balance=20000.0, days=90),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # Premium: 5% annual = (balance * 0.05) / 12 monthly
        self.assertEqual(deposits[0].balance, 10041.67)  # 10000 + (10000 * 0.05 / 12)
        self.assertEqual(deposits[1].balance, 20083.33)  # 20000 + (20000 * 0.05 / 12)

    def test_update_balance_premium_not_eligible_too_few_days(self):
        """Test premium plan with <= 45 days earns no interest"""
        deposits = [
            TimeDeposit(id=1, planType='premium', balance=10000.0, days=45),
            TimeDeposit(id=2, planType='premium', balance=5000.0, days=20),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # No interest applied
        self.assertEqual(deposits[0].balance, 10000.0)
        self.assertEqual(deposits[1].balance, 5000.0)

    def test_update_balance_premium_not_eligible_not_over_30_days(self):
        """Test premium plan must also have > 30 days (not just > 45)"""
        deposits = [
            TimeDeposit(id=1, planType='premium', balance=5000.0, days=25),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # No interest applied (days <= 30)
        self.assertEqual(deposits[0].balance, 5000.0)

    def test_update_balance_basic_eligible(self):
        """Test basic plan with > 30 days earns 1% interest"""
        deposits = [
            TimeDeposit(id=1, planType='basic', balance=2000.0, days=31),
            TimeDeposit(id=2, planType='basic', balance=3000.0, days=60),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # Basic: 1% annual = (balance * 0.01) / 12 monthly
        self.assertEqual(deposits[0].balance, 2001.67)  # 2000 + (2000 * 0.01 / 12)
        self.assertEqual(deposits[1].balance, 3002.5)   # 3000 + (3000 * 0.01 / 12)

    def test_update_balance_basic_not_eligible(self):
        """Test basic plan with <= 30 days earns no interest"""
        deposits = [
            TimeDeposit(id=1, planType='basic', balance=2000.0, days=30),
            TimeDeposit(id=2, planType='basic', balance=1500.0, days=15),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # No interest applied
        self.assertEqual(deposits[0].balance, 2000.0)
        self.assertEqual(deposits[1].balance, 1500.0)

    def test_update_balance_mixed_plan_types(self):
        """Test multiple deposits with different plan types and eligibility"""
        deposits = [
            TimeDeposit(id=1, planType='student', balance=1000.0, days=60),    # Eligible
            TimeDeposit(id=2, planType='student', balance=1000.0, days=20),    # Not eligible
            TimeDeposit(id=3, planType='premium', balance=10000.0, days=90),   # Eligible
            TimeDeposit(id=4, planType='premium', balance=10000.0, days=40),   # Not eligible
            TimeDeposit(id=5, planType='basic', balance=2000.0, days=45),      # Eligible
            TimeDeposit(id=6, planType='basic', balance=2000.0, days=25),      # Not eligible
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # Verify each deposit
        self.assertEqual(deposits[0].balance, 1002.5)    # Student: interest applied
        self.assertEqual(deposits[1].balance, 1000.0)    # Student: no interest (days <= 30)
        self.assertEqual(deposits[2].balance, 10041.67)  # Premium: interest applied
        self.assertEqual(deposits[3].balance, 10000.0)   # Premium: no interest (days <= 45)
        self.assertEqual(deposits[4].balance, 2001.67)   # Basic: interest applied
        self.assertEqual(deposits[5].balance, 2000.0)    # Basic: no interest (days <= 30)

    def test_update_balance_edge_cases(self):
        """Test boundary conditions for each plan type"""
        deposits = [
            # Student: exactly 31 days (should earn interest)
            TimeDeposit(id=1, planType='student', balance=1000.0, days=31),
            # Student: exactly 365 days (should earn interest)
            TimeDeposit(id=2, planType='student', balance=1000.0, days=365),
            # Premium: exactly 46 days (should earn interest)
            TimeDeposit(id=3, planType='premium', balance=10000.0, days=46),
            # Basic: exactly 31 days (should earn interest)
            TimeDeposit(id=4, planType='basic', balance=2000.0, days=31),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        self.assertEqual(deposits[0].balance, 1002.5)    # Student: interest applied
        self.assertEqual(deposits[1].balance, 1002.5)    # Student: interest applied
        self.assertEqual(deposits[2].balance, 10041.67)  # Premium: interest applied
        self.assertEqual(deposits[3].balance, 2001.67)   # Basic: interest applied

    def test_update_balance_large_balances(self):
        """Test with large balance values to ensure rounding works correctly"""
        deposits = [
            TimeDeposit(id=1, planType='basic', balance=1234567.89, days=45),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        # Basic: 1% annual = (1234567.89 * 0.01) / 12 = 1028.81
        expected = round(1234567.89 + 1028.81, 2)
        self.assertEqual(deposits[0].balance, expected)
