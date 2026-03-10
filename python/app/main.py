from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.adapters.api import routes
from app.adapters.database.config import DatabaseSettings, init_db, create_tables, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events"""
    # Startup: Initialize database
    settings = DatabaseSettings()
    init_db(settings)

    # Create tables (for development - use Alembic migrations in production)
    await create_tables()

    print(f"Database initialized: {settings.database_url}")

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
