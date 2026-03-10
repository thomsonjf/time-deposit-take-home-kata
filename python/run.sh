#!/bin/bash

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
