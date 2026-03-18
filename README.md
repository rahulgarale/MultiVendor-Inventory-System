# Multi-Vendor Inventory System

Backend service for managing product inventory with many-to-many vendor relationships, stock tracking, and purchase ordering.

## Tech Stack

- FastAPI
- SQLAlchemy + PostgreSQL
- Pydantic v2

## Setup

### 1. Create PostgreSQL database

```sql
CREATE DATABASE inventory_db;
```

### 2. Create virtual environment and install dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.sample .env      # Windows
```

Update `.env` with your PostgreSQL username and password.

### 4. Start the server

```bash
python -m app.main
```

or using uvicorn directly:

```bash
uvicorn app.main:app --reload
```

### 5. (Optional) Seed sample data

```bash
python seed_database.py
```


API docs available at: `http://localhost:8000/docs`

### Run tests

```bash
pytest tests/ -v
```

## Project Structure

```
app/
  core/         - Config, logging, custom exceptions
  db/models/    - SQLAlchemy models
  repositories/ - Database access layer
  services/     - Business logic
  routes/       - API endpoints
  schemas/      - Pydantic request/response schemas
```
