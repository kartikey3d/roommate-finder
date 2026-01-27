# 🏠 Roommate Finder

A production-ready backend API for an intelligent roommate matching platform. Built with clean architecture principles, this system provides deterministic, explainable matching algorithms while maintaining scalability and code quality.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Overview

Roommate Finder is a sophisticated matching system that helps users find compatible roommates based on multiple factors including:

- **Budget compatibility** - Find roommates within your price range
- **Location proximity** - Match with people in your area
- **Lifestyle preferences** - Sleep schedules, cleanliness, smoking/drinking habits
- **Move-in availability** - Coordinate timing with potential roommates
- **Explainable matching** - Every match includes detailed compatibility reasons

Unlike simple filtering systems, our matching engine uses weighted heuristics to provide compatibility scores (0-100) with transparent explanations for each match.

## ✨ Features

### Core Functionality
- 🔐 **JWT Authentication** - Secure user registration and login
- 👤 **Profile Management** - Comprehensive user profiles with preferences
- 🎯 **Intelligent Matching** - Multi-factor compatibility scoring
- 💬 **Messaging System** - In-app communication between matched users
- 📊 **Reputation System** - User trust scores and behavior tracking
- 🏢 **Room Listings** - Post and browse available accommodations

### Technical Highlights
- ⚡ **Async/Await** - Full asynchronous request handling
- 🧪 **Clean Architecture** - Framework-agnostic domain logic
- 📝 **Type-Safe** - Complete Pydantic validation
- 🔄 **Event-Driven** - Background processing with Celery
- 🧩 **Explainable AI** - Transparent matching decisions
- 📈 **Scalable Design** - Built for 1,000+ concurrent users

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Framework** | FastAPI 0.109+ |
| **Language** | Python 3.11+ |
| **Database** | PostgreSQL 14+ |
| **ORM** | SQLAlchemy 2.0 (async) |
| **Migrations** | Alembic |
| **Cache** | Redis 6+ |
| **Queue** | Celery + Redis |
| **Validation** | Pydantic v2 |
| **Authentication** | JWT + bcrypt |
| **Testing** | pytest + pytest-asyncio |

## 📁 Project Structure

```
roommate-finder/
├── app/
│   ├── api/                    # API layer (FastAPI routes)
│   │   ├── routes/
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── profiles.py    # Profile management
│   │   │   ├── preferences.py # User preferences
│   │   │   ├── matches.py     # Matching endpoints
│   │   │   └── messages.py    # Messaging system
│   │   └── dependencies.py    # FastAPI dependencies (auth, etc.)
│   │
│   ├── core/                   # Domain logic (pure Python)
│   │   └── matching/
│   │       └── engine.py      # Matching algorithm
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── base.py            # Base model & DB setup
│   │   ├── user.py            # User, Profile, Preferences
│   │   ├── listing.py         # Room listings
│   │   └── message.py         # Messages & conversations
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── user.py            # User-related schemas
│   │   ├── preferences.py     # Preference schemas
│   │   └── messages.py        # Message schemas
│   │
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── profile_service.py # Profile operations
│   │   ├── preferences_service.py
│   │   ├── matching_service.py
│   │   └── messages_service.py
│   │
│   ├── workers/                # Background tasks
│   │   └── tasks.py           # Celery tasks
│   │
│   ├── events/                 # Event system
│   │   └── definitions.py     # Event types & publisher
│   │
│   ├── tests/                  # Test suite
│   │   ├── unit/              # Unit tests
│   │   └── integration/       # Integration tests
│   │
│   ├── config.py              # Configuration management
│   └── main.py                # Application entry point
│
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── Makefile                   # Common commands
└── README.md                  # This file
```

### Architecture Principles

**Clean Architecture**
- `core/` - Pure domain logic, no framework dependencies
- `services/` - Orchestration layer between API and core
- `api/` - Thin routing layer, delegates to services

**Event-Driven Design**
- Profile/preference updates emit events
- Celery workers handle async processing
- Match recomputation runs in background

## 🚀 Quick Start

### Prerequisites

Ensure you have the following installed:
- Python 3.11 or higher
- PostgreSQL 14 or higher
- Redis 6 or higher

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/roommate-finder.git
   cd roommate-finder
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

5. **Create database**
   ```bash
   createdb roommate_db
   ```

6. **Run migrations**
   ```bash
   cd app
   alembic upgrade head
   ```

### Running the Application

#### Option 1: Development Mode (Single Command)

```bash
cd app
uvicorn main:app --reload --port 8000
```

#### Option 2: Full Stack (Recommended)

Run these in separate terminals:

```bash
# Terminal 1: API Server
cd app
uvicorn main:app --reload --port 8000

# Terminal 2: Celery Worker
cd app
celery -A workers.tasks worker --loglevel=info

# Terminal 3: Celery Beat (optional - for periodic tasks)
cd app
celery -A workers.tasks beat --loglevel=info
```

#### Option 3: Using Makefile

```bash
# Start API server
make run

# Start Celery worker
make celery

# Run tests
make test
```

### Verify Installation

Open your browser and visit:
- **API Health Check**: http://localhost:8000/health
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative Docs (ReDoc)**: http://localhost:8000/redoc

Expected health check response:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root (see `.env.example` for template):

#### Required Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/roommate_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Security
BCRYPT_ROUNDS=12
```

#### Optional Variables

```bash
# Application
DEBUG=False
API_VERSION=v1

# Matching Algorithm
MATCHING_VERSION=v1
MATCHING_MAX_DISTANCE_KM=50.0
MATCHING_MIN_SCORE_THRESHOLD=30

# Rate Limiting
RATE_LIMIT_MESSAGES_PER_HOUR=50
RATE_LIMIT_MATCH_REQUESTS_PER_DAY=100

# Reputation
REPUTATION_INITIAL_SCORE=100
REPUTATION_GHOSTING_PENALTY=-10
REPUTATION_SPAM_PENALTY=-5
```

### Generating Secure Keys

```bash
# Generate JWT secret key
openssl rand -hex 32

# Or using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## 📚 API Documentation

### Accessing API Docs

Once the server is running, visit:

**Swagger UI** (Interactive): http://localhost:8000/docs
- Try out endpoints directly in the browser
- See request/response schemas
- Test authentication

**ReDoc** (Reference): http://localhost:8000/redoc
- Clean, readable documentation
- Better for API overview

### API Endpoints

#### Authentication
```
POST   /api/v1/auth/signup     - Register new user
POST   /api/v1/auth/login      - Login and get JWT token
GET    /api/v1/auth/me         - Get current user info
```

#### Profiles
```
POST   /api/v1/profiles        - Create profile
GET    /api/v1/profiles/me     - Get own profile
PUT    /api/v1/profiles/me     - Update profile
DELETE /api/v1/profiles/me     - Delete profile
GET    /api/v1/profiles/{id}   - View user profile
```

#### Preferences
```
POST   /api/v1/preferences     - Set preferences
GET    /api/v1/preferences/me  - Get own preferences
PUT    /api/v1/preferences/me  - Update preferences
```

#### Matching
```
GET    /api/v1/matches         - Get ranked matches
GET    /api/v1/matches/explain/{id} - Detailed match explanation
```

#### Messaging
```
POST   /api/v1/messages        - Send message
GET    /api/v1/messages        - Get messages
GET    /api/v1/messages/conversations - List conversations
POST   /api/v1/messages/mark-read - Mark as read
```

### Authentication

Most endpoints require authentication. Include JWT token in headers:

```bash
Authorization: Bearer <your_jwt_token>
```

Example with curl:
```bash
curl -H "Authorization: Bearer eyJ0eXAi..." \
     http://localhost:8000/api/v1/matches
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest app/tests/test_matching_engine.py -v

# Run only unit tests
pytest app/tests/unit/ -v
```

### Test Coverage

The project aims for:
- **90%+ coverage** for core matching logic
- **80%+ coverage** for services
- **70%+ coverage** overall

View coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## 🔄 Database Migrations

### Create Migration

```bash
cd app
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# View history
alembic history
```

## 📊 Matching Algorithm

### Score Components (Total: 100 points)

| Factor | Weight | Description |
|--------|--------|-------------|
| Budget | 20 | Overlap in budget ranges |
| Location | 25 | Geographic proximity (km) |
| Cleanliness | 15 | Lifestyle compatibility |
| Sleep Schedule | 10 | Sleep pattern alignment |
| Lifestyle | 15 | Smoking, pets, guests |
| Availability | 10 | Move-in date overlap |
| Reputation | 5 | User trust score bonus |

### Match Quality

- **90-100**: Excellent match ⭐⭐⭐⭐⭐
- **70-89**: Good match ⭐⭐⭐⭐
- **50-69**: Moderate match ⭐⭐⭐
- **30-49**: Weak match ⭐⭐
- **0-29**: Poor match (filtered out)

### Explainability

Every match includes:
- Overall compatibility score
- Top 3 reasons for the match (with point values)
- List of potential conflicts
- Distance between users
- Budget overlap range

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints everywhere
- Write docstrings for all functions
- Keep functions under 50 lines
- Maintain test coverage

### Running Linters

```bash
# Format code
black app/

# Sort imports
isort app/

# Check types
mypy app/

# Lint code
flake8 app/
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when running
- **Issues**: [GitHub Issues](https://github.com/yourusername/roommate-finder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/roommate-finder/discussions)

## 🗺️ Roadmap

### Current Version (v1.0)
- ✅ User authentication
- ✅ Profile & preferences management
- ✅ Intelligent matching algorithm
- ✅ Messaging system
- ✅ Reputation tracking

### Planned Features
- [ ] Email verification
- [ ] Photo uploads for profiles and listings
- [ ] Real-time messaging (WebSocket)
- [ ] Advanced search filters
- [ ] Mobile app API support
- [ ] Payment integration for deposits
- [ ] Background check integration
- [ ] In-app video calls

## Author

 [@kartikey3d](https://github.com/kartikey3d)

## Acknowledgments

- FastAPI for the amazing framework
- SQLAlchemy for robust ORM
- PostgreSQL for reliable data storage
- The open-source community

---

**Made with ❤️ for helping people find their perfect roommates**
