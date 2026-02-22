# API Norte - Asset Management API

FastAPI backend for the Asset Management System (Nuxt frontend).

## Features

- ✅ JWT Authentication
- ✅ SQLite Database with SQLAlchemy
- ✅ Pydantic schemas for validation
- ✅ Comprehensive logging
- ✅ Linting with Ruff
- ✅ RESTful API design
- ✅ CORS enabled for frontend integration
- ✅ Comprehensive test suite (138 tests)

## Project Structure

```
api/
├── core/               # Core configuration and utilities
│   ├── config.py       # Settings and environment variables
│   ├── database.py     # Database connection and session
│   ├── security.py     # JWT and password hashing
│   └── logger.py       # Logging configuration
├── models/             # SQLAlchemy models
│   ├── user.py
│   ├── equipment.py
│   ├── event.py
│   ├── bag.py
│   ├── transaction.py
│   ├── reservation.py
│   └── audit_log.py
├── schemas/            # Pydantic schemas
│   ├── user.py
│   ├── equipment.py
│   ├── event.py
│   ├── bag.py
│   ├── transaction.py
│   ├── reservation.py
│   └── audit_log.py
├── routes/             # API endpoints
│   ├── auth.py         # Authentication routes
│   ├── users.py        # User management
│   ├── equipment.py    # Equipment CRUD
│   ├── events.py       # Events CRUD
│   ├── bags.py         # Bags CRUD
│   ├── transactions.py # Transaction tracking
│   ├── reservations.py # Reservations CRUD
│   └── reports.py      # Statistics and reports
├── services/           # Business logic layer
├── utils/              # Utility functions
│   └── auth.py         # Auth dependencies
├── tests/              # Test suite
│   ├── conftest.py     # Shared fixtures
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_equipment.py
│   ├── test_events.py
│   ├── test_bags.py
│   ├── test_transactions.py
│   ├── test_reservations.py
│   ├── test_reports.py
│   └── test_security.py
├── main.py             # FastAPI application
├── requirements.txt    # Python dependencies
├── pyproject.toml      # Ruff configuration
└── pytest.ini          # Pytest configuration
```

## Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set your SECRET_KEY
   ```

4. **Run the API:**
   ```bash
   python main.py
   # or
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access documentation:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update current user profile
- `GET /users/` - List all users (admin only)
- `GET /users/{id}` - Get user by ID (admin only)
- `PUT /users/{id}` - Update user (admin only)
- `DELETE /users/{id}` - Delete user (admin only)

### Equipment
- `GET /equipment/` - List equipment (with filters)
- `GET /equipment/{id}` - Get equipment by ID
- `GET /equipment/qr/{qr_code}` - Get equipment by QR code
- `POST /equipment/` - Create equipment
- `PUT /equipment/{id}` - Update equipment
- `DELETE /equipment/{id}` - Delete equipment

### Events
- `GET /events/` - List events (with filters)
- `GET /events/{id}` - Get event by ID
- `POST /events/` - Create event
- `PUT /events/{id}` - Update event
- `DELETE /events/{id}` - Delete event

### Bags
- `GET /bags/` - List bags
- `GET /bags/{id}` - Get bag by ID
- `POST /bags/` - Create bag
- `PUT /bags/{id}` - Update bag
- `DELETE /bags/{id}` - Delete bag

### Transactions
- `GET /transactions/` - List transactions
- `GET /transactions/{id}` - Get transaction by ID
- `POST /transactions/` - Create transaction
- `PUT /transactions/{id}` - Update transaction
- `DELETE /transactions/{id}` - Delete transaction

### Reservations
- `GET /reservations/` - List reservations
- `GET /reservations/{id}` - Get reservation by ID
- `POST /reservations/` - Create reservation
- `PUT /reservations/{id}` - Update reservation
- `DELETE /reservations/{id}` - Delete reservation

### Reports
- `GET /reports/dashboard` - Dashboard statistics
- `GET /reports/equipment-usage` - Equipment usage report

## Testing

The project has a comprehensive test suite with 138 tests covering all endpoints.

### Run Tests
```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_auth.py

# Run tests matching pattern
pytest -k "login"

# Run with coverage
pytest --cov=.
```

### Test Categories
- **Authentication** (`test_auth.py`) - 9 tests
- **Users** (`test_users.py`) - 16 tests
- **Equipment** (`test_equipment.py`) - 18 tests
- **Events** (`test_events.py`) - Event management tests
- **Bags** (`test_bags.py`) - Bag management tests
- **Transactions** (`test_transactions.py`) - Transaction tests
- **Reservations** (`test_reservations.py`) - Reservation tests
- **Reports** (`test_reports.py`) - Report endpoint tests
- **Security** (`test_security.py`) - Security tests

## Development

### Linting
```bash
ruff check .
ruff check . --fix    # Auto-fix issues
ruff format .         # Format code
```

### Database
The SQLite database file (`api_norte.db`) will be created automatically on first run.

## Authentication

All endpoints (except `/auth/register` and `/auth/login`) require authentication.

Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## Admin Access

Some endpoints require admin role:
- User management (list, get, update, delete users)

Default admin user: `admin` / `admin`

## Notes

- Requires `bcrypt==4.0.1` (passlib compatibility)
- Test database uses `/tmp/test_api_norte.db`
