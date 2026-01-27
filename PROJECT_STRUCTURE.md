# Recommended Project Structure

## Current Structure (Already Good!)

Your current structure follows clean architecture principles and is production-ready. Here's the recommended organization:

```
roommate-finder/
├── app/                           # Main application directory
│   ├── __init__.py
│   │
│   ├── api/                       # API Layer (FastAPI)
│   │   ├── __init__.py
│   │   ├── dependencies.py        # Shared dependencies (auth, etc.)
│   │   └── routes/                # Route handlers
│   │       ├── __init__.py
│   │       ├── auth.py            # Authentication endpoints
│   │       ├── profiles.py        # User profiles
│   │       ├── preferences.py     # User preferences
│   │       ├── matches.py         # Matching endpoints
│   │       ├── messages.py        # Messaging system
│   │       └── listings.py        # Room listings (future)
│   │
│   ├── core/                      # Domain Layer (Pure Python)
│   │   ├── __init__.py
│   │   └── matching/              # Matching engine
│   │       ├── __init__.py
│   │       └── engine.py          # Matching algorithm v1
│   │
│   ├── models/                    # Database Models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── base.py                # Base model & DB setup
│   │   ├── user.py                # User, Profile, Preferences, Reputation
│   │   ├── listing.py             # Room listings
│   │   └── message.py             # Messages & conversations
│   │
│   ├── schemas/                   # Request/Response Schemas (Pydantic)
│   │   ├── __init__.py
│   │   ├── user.py                # User-related schemas
│   │   ├── preferences.py         # Preference schemas
│   │   └── messages.py            # Message schemas
│   │
│   ├── services/                  # Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py        # Authentication logic
│   │   ├── profile_service.py     # Profile management
│   │   ├── preferences_service.py # Preferences management
│   │   ├── matching_service.py    # Matching orchestration
│   │   └── messages_service.py    # Messaging logic
│   │
│   ├── workers/                   # Background Tasks (Celery)
│   │   ├── __init__.py
│   │   └── tasks.py               # Celery task definitions
│   │
│   ├── events/                    # Event System
│   │   ├── __init__.py
│   │   └── definitions.py         # Event types & publisher
│   │
│   ├── db/                        # Database-related
│   │   └── migrations/            # Alembic migrations
│   │       ├── versions/          # Migration files
│   │       ├── env.py             # Alembic environment
│   │       └── script.py.mako     # Migration template
│   │
│   ├── tests/                     # Test Suite
│   │   ├── __init__.py
│   │   ├── conftest.py            # Pytest fixtures
│   │   ├── unit/                  # Unit tests
│   │   │   ├── __init__.py
│   │   │   └── test_matching_engine.py
│   │   └── integration/           # Integration tests
│   │       ├── __init__.py
│   │       ├── test_auth.py
│   │       └── test_matching.py
│   │
│   ├── config.py                  # Configuration management
│   └── main.py                    # FastAPI application entry point
│
├── scripts/                       # Utility scripts (optional)
│   ├── seed_data.py               # Seed test data
│   └── backup_db.sh               # Database backup
│
├── docs/                          # Additional documentation (optional)
│   ├── api.md                     # API documentation
│   ├── architecture.md            # Architecture overview
│   └── deployment.md              # Deployment guide
│
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Python dependencies
├── requirements-dev.txt           # Development dependencies (optional)
├── Makefile                       # Common commands
├── pytest.ini                     # Pytest configuration
├── alembic.ini                    # Alembic configuration
├── LICENSE                        # License file
└── README.md                      # Project documentation
```

## Optional Additions

### 1. Development Dependencies File

Create `requirements-dev.txt` for development tools:

```text
# Testing
pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
black==24.1.1
isort==5.13.2
flake8==7.0.0
mypy==1.8.0
pylint==3.0.3

# Documentation
mkdocs==1.5.3
mkdocs-material==9.5.3

# Debugging
ipdb==0.13.13
ipython==8.20.0
```

### 2. Pytest Configuration

Create `pytest.ini`:

```ini
[pytest]
testpaths = app/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --cov=app
    --cov-report=term-missing
    --cov-report=html
asyncio_mode = auto
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

### 3. Pre-commit Configuration

Create `.pre-commit-config.yaml` (optional):

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
```

### 4. Docker Support (Optional)

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - .env

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: roommate_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:6
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A app.workers.tasks worker --loglevel=info
    depends_on:
      - db
      - redis
    env_file:
      - .env

volumes:
  postgres_data:
```

## File Naming Conventions

### Python Files
- **Modules**: `snake_case.py` (e.g., `auth_service.py`)
- **Classes**: `PascalCase` (e.g., `AuthService`, `UserProfile`)
- **Functions**: `snake_case` (e.g., `create_user`, `get_matches`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRIES`, `API_VERSION`)

### Test Files
- Pattern: `test_*.py`
- Example: `test_auth_service.py`, `test_matching_engine.py`

### Migration Files
- Auto-generated by Alembic
- Pattern: `{revision}_{description}.py`
- Example: `a1b2c3d4e5f6_add_messaging_tables.py`

## Import Organization

Within each file, organize imports in this order:

```python
# 1. Standard library imports
import os
from datetime import datetime
from typing import Optional, List

# 2. Third-party imports
from fastapi import APIRouter, Depends
from sqlalchemy import select
from pydantic import BaseModel

# 3. Local application imports
from models.user import User
from schemas.user import UserResponse
from services.auth_service import AuthService
```

## Why This Structure Works

### ✅ Separation of Concerns
- API layer handles HTTP
- Services handle business logic
- Core contains pure domain logic
- Models handle data persistence

### ✅ Testability
- Pure functions in `core/` are easy to test
- Services can be mocked
- Integration tests cover full flows

### ✅ Scalability
- Easy to add new routes
- Services can be split into microservices
- Core logic remains unchanged

### ✅ Maintainability
- Clear module boundaries
- Each file has single responsibility
- Easy to locate functionality

## No Refactoring Needed!

Your current structure is already following best practices. The only additions recommended are:

1. ✅ Add `__init__.py` files (if missing)
2. ✅ Add `pytest.ini` for test configuration
3. ✅ Add `requirements-dev.txt` for dev tools
4. ⚠️ Optional: Docker setup for deployment
5. ⚠️ Optional: Pre-commit hooks for code quality

Your architecture is **production-ready** as-is! 🎉