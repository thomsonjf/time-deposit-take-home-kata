from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to the time deposits API"}

@app.get("/time-deposits")
async def get_deposits():
    return {"message": "Deposits fetched successfully", "data": []}

@app.post("/time-deposits")
async def update_deposits():
    return {"message": "Deposits Updated"}    


