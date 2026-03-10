#!/usr/bin/env python
"""CLI script to seed the database with sample data"""
import asyncio
import sys

sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.adapters.database.config import DatabaseSettings
from app.adapters.database.repositories import PostgresTimeDepositRepository, PostgresWithdrawalRepository
from app.adapters.database.seed_data import seed_database


async def main():
    """Seed the database with sample data"""
    print("Running database seeders...")

    # Create settings
    settings = DatabaseSettings()

    # Create a new engine and session factory for seeding
    # Use NullPool to avoid greenlet issues with concurrent access
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        poolclass=NullPool
    )
    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create session and repositories
    async with AsyncSessionLocal() as session:
        deposit_repository = PostgresTimeDepositRepository(session)
        withdrawal_repository = PostgresWithdrawalRepository(session)

        try:
            # Seed data
            deposits = await seed_database(deposit_repository, withdrawal_repository)

            print(f"Successfully created {len(deposits)} time deposits with withdrawals:")
            for deposit in deposits:
                print(f"  - ID: {deposit.id}, Plan: {deposit.planType}, Days: {deposit.days}, Balance: ${deposit.balance}")

        except Exception as e:
            print(f"Error seeding database: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
