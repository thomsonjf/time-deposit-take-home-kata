# Time Deposit API

A FastAPI-based microservice for managing time deposits with interest calculations, built following hexagonal architecture principles.

The architecture benefits from:

- **Technology independence**: Domain logic doesn't depend on frameworks or databases
- **Testability**: Easy to test business logic in isolation - a test of services is included
- **Flexibility**: Can swap database or API framework without touching domain code
- **Clear dependencies**: Dependencies flow from adapters > application > domain

## Approach

As per the instructions and business requirements:

- Expanded the scope of the interest method testing to ensure future changes don't break it
- Implemented two API endpoints - one to get all balances with withdrawals, another to update balances
- Database scaffolding and seeders (dev) and fixtures (test) for the two tables
- Wired up logic to calculate monthly interest to to the updateBalances function
- Refactored TimeDepositCalculator to use a registry style pattern for different plan type calculations - this allows for future development without modifying existing code (open/close principle).
- Docker launch scripts and configuration

## Future expansion

With more time, I would next approach the following:

- Expand the types of test, potentially to include contract testing
- Revamp the scalability of the update_balances method and test with a larger data set - currently it reads all TimeDeposit records from the database and issues an update - this isn't efficient. It would benefit from pagination and bulk updates - some notes are in a TODO in `services.py`.

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15 (or use Docker Compose)

## Installation

### 1. Create and activate virtual environment

```bash
cd python
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing
```

### 3. Set up environment variables

```bash
cp .env.example .env
# Edit .env if needed (default values work with docker-compose)
```

## Running the Application

### Option 1: Docker Compose (Recommended)

Start both API and database with auto-seeding:

```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000`

**Note**: By default, the database is automatically seeded with sample data on startup (controlled by `SEED_DB=true` in docker-compose.yml). To disable auto-seeding, set `SEED_DB: "false"` in the environment section.

### Option 2: Local Development

Start PostgreSQL (if not using Docker):

```bash
docker-compose up db
```

Run the API locally:

```bash
cd python
source .venv/bin/activate

# Set PYTHONPATH to include the current directory
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the application
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Base URL: `/time-deposits`

**GET /** - Retrieve all time deposits with withdrawals

```
curl -X 'GET' \
  'http://127.0.0.1:8000/time-deposits/' \
  -H 'accept: application/json'
```

**PUT /balances** - Update all deposit balances with interest

```
curl -X 'PUT' \
  'http://127.0.0.1:8000/time-deposits/balances' \
  -H 'accept: application/json'
```

### API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- OpenAI: `http://localhost:8000/openai.json`
- ReDoc: `http://localhost:8000/redoc`

## Testing

### Run Tests with Testcontainers

The integration tests use testcontainers to spin up a real PostgreSQL instance:

```bash
pytest tests/
```

### Test Coverage

```bash
pytest --cov=app tests/
```

## Database Management

### Create Tables

Tables are automatically created on application startup (see `main.py:16`).

### Seed Database with Sample Data

**For Docker Compose:**
Sample data is automatically seeded when `SEED_DB=true` (default in docker-compose.yml).

**For Local Development:**
```bash
cd python
source .venv/bin/activate
export PYTHONPATH=".:$PYTHONPATH"
python seed_db.py
```

### Database Schema

**timeDeposits**
- id (INTEGER, PK)
- plan_type (VARCHAR)
- days (INTEGER)
- balance (FLOAT)

**withdrawals**
- id (INTEGER, PK)
- time_deposit_id (INTEGER, FK)
- amount (FLOAT)
- date (TIMESTAMP)
