from fastapi import APIRouter, Depends

from application.services import TimeDepositService

router = APIRouter()

def get_service():
    return TimeDepositService

@router.get("/deposits")
def get_items(service: TimeDepositService = Depends(get_service)):
    return service.get_time_deposits()

@router.post("/deposits")
def update_items(service: TimeDepositService = Depends(get_service)):
    return service.update_time_deposits()
