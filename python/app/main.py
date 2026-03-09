from contextlib import asynccontextmanager
from fastapi import FastAPI

from adapters.api import routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Database setup will go here
    yield

app = FastAPI(title="API For TimeDeposits", 
              description="This API handles listing and updating all deposit items",
              lifespan=lifespan)

app.include_router(routes.router, prefix="/time-deposits", tags=["time-deposits"]) 


