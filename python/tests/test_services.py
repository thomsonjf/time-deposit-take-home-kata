import pytest
import asyncio
import docker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from testcontainers.postgres import PostgresContainer

from app.domain.models import TimeDeposit
from app.application.services import TimeDepositService, TimeDepositCalculator
from app.adapters.database.repositories import PostgresTimeDepositRepository
from app.adapters.database.models import TimeDepositORM, WithdrawalORM
from app.adapters.database.config import Base


def is_docker_available():
    """Check if Docker is available and accessible"""
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


# Mark to skip integration tests if Docker is not available
docker_required = pytest.mark.skipif(
    not is_docker_available(),
    reason="Docker is not available - skipping integration tests"
)


@pytest.fixture(scope="module")
def postgres_container():
    """Start a PostgreSQL container for testing"""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def engine(postgres_container):
    """Create async engine connected to test database"""
    # Get connection URL and convert to async format
    connection_url = postgres_container.get_connection_url()
    async_url = connection_url.replace("psycopg2", "asyncpg").replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(async_url, echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture
async def session(engine):
    """Create a fresh session for each test"""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def repository(session):
    """Create repository instance"""
    return PostgresTimeDepositRepository(session)


@pytest.fixture
async def service(repository):
    """Create service instance"""
    return TimeDepositService(repository)


@pytest.fixture
async def sample_deposits(session):
    """Create sample deposits in database"""
    deposits = [
        TimeDepositORM(plan_type="student", days=60, balance=1000.0),
        TimeDepositORM(plan_type="student", days=180, balance=5000.0),
        TimeDepositORM(plan_type="student", days=30, balance=2000.0),  # Not eligible
        TimeDepositORM(plan_type="premium", days=90, balance=10000.0),
        TimeDepositORM(plan_type="premium", days=45, balance=3000.0),  # Not eligible
        TimeDepositORM(plan_type="basic", days=45, balance=2000.0),
        TimeDepositORM(plan_type="basic", days=20, balance=1500.0),  # Not eligible
    ]

    for deposit in deposits:
        session.add(deposit)

    await session.commit()

    return deposits


@docker_required
class TestTimeDepositService:
    """Test TimeDepositService methods - requires Docker"""

    @pytest.mark.asyncio
    async def test_get_time_deposits_empty(self, service):
        """Test getting deposits when database is empty"""
        deposits = await service.get_time_deposits()
        assert deposits == []

    @pytest.mark.asyncio
    async def test_get_time_deposits_with_data(self, service, sample_deposits):
        """Test getting all deposits returns correct data"""
        deposits = await service.get_time_deposits()

        assert len(deposits) == 7
        assert all(isinstance(d, TimeDeposit) for d in deposits)

        # Verify data
        student_deposits = [d for d in deposits if d.planType == "student"]
        assert len(student_deposits) == 3

        premium_deposits = [d for d in deposits if d.planType == "premium"]
        assert len(premium_deposits) == 2

        basic_deposits = [d for d in deposits if d.planType == "basic"]
        assert len(basic_deposits) == 2

    @pytest.mark.asyncio
    async def test_update_time_deposits_calculates_interest(self, service, sample_deposits, session):
        """Test that update calculates and persists interest correctly"""
        # Get initial balances
        initial_deposits = await service.get_time_deposits()
        initial_balances = {d.id: d.balance for d in initial_deposits}

        # Update deposits
        count = await service.update_time_deposits()
        await session.commit()

        # Verify count
        assert count == 7

        # Get updated deposits
        updated_deposits = await service.get_time_deposits()

        # Check student deposits
        student_60_days = next(d for d in updated_deposits if d.planType == "student" and d.days == 60)
        assert student_60_days.balance == 1002.5  # 1000 + (1000 * 0.03 / 12)

        student_180_days = next(d for d in updated_deposits if d.planType == "student" and d.days == 180)
        assert student_180_days.balance == 5012.5  # 5000 + (5000 * 0.03 / 12)

        student_30_days = next(d for d in updated_deposits if d.planType == "student" and d.days == 30)
        assert student_30_days.balance == 2000.0  # No interest (days <= 30)

        # Check premium deposits
        premium_90_days = next(d for d in updated_deposits if d.planType == "premium" and d.days == 90)
        assert premium_90_days.balance == 10041.67  # 10000 + (10000 * 0.05 / 12)

        premium_45_days = next(d for d in updated_deposits if d.planType == "premium" and d.days == 45)
        assert premium_45_days.balance == 3000.0  # No interest (days <= 45)

        # Check basic deposits
        basic_45_days = next(d for d in updated_deposits if d.planType == "basic" and d.days == 45)
        assert basic_45_days.balance == 2001.67  # 2000 + (2000 * 0.01 / 12)

        basic_20_days = next(d for d in updated_deposits if d.planType == "basic" and d.days == 20)
        assert basic_20_days.balance == 1500.0  # No interest (days <= 30)

    @pytest.mark.asyncio
    async def test_update_multiple_times_compounds_interest(self, service, sample_deposits, session):
        """Test that calling update multiple times compounds interest correctly"""
        # First update
        await service.update_time_deposits()
        await session.commit()

        deposits_after_first = await service.get_time_deposits()
        student_deposit = next(d for d in deposits_after_first if d.planType == "student" and d.days == 60)
        balance_after_first = student_deposit.balance
        assert balance_after_first == 1002.5

        # Second update (should compound on new balance)
        await service.update_time_deposits()
        await session.commit()

        deposits_after_second = await service.get_time_deposits()
        student_deposit = next(d for d in deposits_after_second if d.planType == "student" and d.days == 60)
        balance_after_second = student_deposit.balance

        # Should be: 1002.5 + (1002.5 * 0.03 / 12) = 1005.01
        assert balance_after_second == pytest.approx(1005.01, rel=0.01)


class TestTimeDepositCalculator:
    """Test TimeDepositCalculator logic"""

    def test_calculator_student_eligible(self):
        """Test calculator applies correct interest for eligible student deposits"""
        deposits = [
            TimeDeposit(id=1, planType="student", balance=1000.0, days=60),
            TimeDeposit(id=2, planType="student", balance=5000.0, days=365),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 1002.5
        assert deposits[1].balance == 5012.5

    def test_calculator_student_not_eligible_low_days(self):
        """Test calculator doesn't apply interest for student deposits with <= 30 days"""
        deposits = [
            TimeDeposit(id=1, planType="student", balance=1000.0, days=30),
            TimeDeposit(id=2, planType="student", balance=2000.0, days=15),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 1000.0
        assert deposits[1].balance == 2000.0

    def test_calculator_student_not_eligible_high_days(self):
        """Test calculator doesn't apply interest for student deposits with >= 366 days"""
        deposits = [
            TimeDeposit(id=1, planType="student", balance=1000.0, days=366),
            TimeDeposit(id=2, planType="student", balance=2000.0, days=400),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 1000.0
        assert deposits[1].balance == 2000.0

    def test_calculator_premium_eligible(self):
        """Test calculator applies correct interest for eligible premium deposits"""
        deposits = [
            TimeDeposit(id=1, planType="premium", balance=10000.0, days=46),
            TimeDeposit(id=2, planType="premium", balance=20000.0, days=90),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 10041.67
        assert deposits[1].balance == 20083.33

    def test_calculator_premium_not_eligible(self):
        """Test calculator doesn't apply interest for premium deposits with <= 45 days"""
        deposits = [
            TimeDeposit(id=1, planType="premium", balance=10000.0, days=45),
            TimeDeposit(id=2, planType="premium", balance=5000.0, days=20),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 10000.0
        assert deposits[1].balance == 5000.0

    def test_calculator_basic_eligible(self):
        """Test calculator applies correct interest for eligible basic deposits"""
        deposits = [
            TimeDeposit(id=1, planType="basic", balance=2000.0, days=31),
            TimeDeposit(id=2, planType="basic", balance=3000.0, days=60),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 2001.67
        assert deposits[1].balance == 3002.5

    def test_calculator_basic_not_eligible(self):
        """Test calculator doesn't apply interest for basic deposits with <= 30 days"""
        deposits = [
            TimeDeposit(id=1, planType="basic", balance=2000.0, days=30),
            TimeDeposit(id=2, planType="basic", balance=1500.0, days=15),
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 2000.0
        assert deposits[1].balance == 1500.0

    def test_calculator_mixed_deposits(self):
        """Test calculator handles mixed deposit types correctly"""
        deposits = [
            TimeDeposit(id=1, planType="student", balance=1000.0, days=60),   # Eligible
            TimeDeposit(id=2, planType="student", balance=1000.0, days=20),   # Not eligible
            TimeDeposit(id=3, planType="premium", balance=10000.0, days=90),  # Eligible
            TimeDeposit(id=4, planType="premium", balance=10000.0, days=40),  # Not eligible
            TimeDeposit(id=5, planType="basic", balance=2000.0, days=45),     # Eligible
            TimeDeposit(id=6, planType="basic", balance=2000.0, days=25),     # Not eligible
        ]

        calc = TimeDepositCalculator()
        calc.update_balance(deposits)

        assert deposits[0].balance == 1002.5     # Student: interest applied
        assert deposits[1].balance == 1000.0     # Student: no interest
        assert deposits[2].balance == 10041.67   # Premium: interest applied
        assert deposits[3].balance == 10000.0    # Premium: no interest
        assert deposits[4].balance == 2001.67    # Basic: interest applied
        assert deposits[5].balance == 2000.0     # Basic: no interest
