#!/usr/bin/env python
"""CLI script to seed the database with sample data"""
import asyncio
import sys

sys.path.insert(0, '.')

from app.adapters.database.config import DatabaseSettings, init_db
from app.adapters.database.repositories import PostgresTimeDepositRepository
from app.adapters.database.seed_data import seed_database


async def main():
    """Seed the database with sample data"""
    print("Running database seeders...")

    # Initialize database
    settings = DatabaseSettings()
    init_db(settings)

    # Import AsyncSessionLocal after init_db to ensure it's initialized
    from app.adapters.database import config

    # Create session and repository
    async with config.AsyncSessionLocal() as session:
        repository = PostgresTimeDepositRepository(session)

        try:
            # Seed data
            deposits = await seed_database(repository)

            print(f"Successfully created {len(deposits)} time deposits:")
            for deposit in deposits:
                print(f"  - ID: {deposit.id}, Plan: {deposit.planType}, Days: {deposit.days}, Balance: ${deposit.balance}")

        except Exception as e:
            print(f"Error seeding database: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
