from contextlib import asynccontextmanager
from fastapi import FastAPI
import os

from app.adapters.api import routes
from app.adapters.database.config import DatabaseSettings, init_db, create_tables, engine
from app.adapters.database.repositories import PostgresTimeDepositRepository, PostgresWithdrawalRepository
from app.adapters.database.seed_data import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events"""
    # Startup: Initialize database
    settings = DatabaseSettings()
    init_db(settings)

    # Create tables (for development - use Alembic migrations in production)
    await create_tables()

    print(f"Database initialized: {settings.database_url}")

    # Seed database if SEED_DB environment variable is set
    if os.getenv("SEED_DB", "false").lower() == "true":
        print("Seeding database with sample data...")
        # Import AsyncSessionLocal after init_db() has been called
        from app.adapters.database import config
        async with config.AsyncSessionLocal() as session:
            deposit_repository = PostgresTimeDepositRepository(session)
            withdrawal_repository = PostgresWithdrawalRepository(session)
            deposits = await seed_database(deposit_repository, withdrawal_repository)
            print(f"Successfully seeded {len(deposits)} time deposits with withdrawals")

    yield

    # Shutdown: Close database connections
    if engine:
        await engine.dispose()
        print("Database connections closed")


app = FastAPI(
    title="API For TimeDeposits",
    description="This API handles listing and updating all deposit items",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(routes.router, prefix="/time-deposits", tags=["time-deposits"]) 
