# API Norte - Asset Management API

FastAPI backend for the Asset Management System (Nuxt frontend).

## Features

- JWT Authentication with HTTP-only cookies
- SQLite Database with SQLAlchemy ORM
- Pydantic schemas for validation
- Comprehensive logging
- Linting with Ruff
- RESTful API design
- CORS enabled for frontend integration
- Repository pattern for data access
- Comprehensive test suite

## Project Structure

```
api/
├── core/               # Core configuration and utilities
│   ├── config.py       # Settings and environment variables
│   ├── database.py     # Database connection and session
│   ├── security.py     # JWT and password hashing
│   └── logger.py       # Logging configuration
├── models/             # SQLAlchemy models (entities)
│   ├── user.py        # User entity
│   ├── equipment.py    # Equipment entity (+ current_event_id)
│   ├── event.py       # Event entity
│   ├── bag.py         # Bag entity (+ current_event_id)
│   ├── transaction.py # Transaction entity
│   ├── reservation.py # Reservation entity
│   └── audit_log.py   # Audit log entity
├── schemas/            # Pydantic schemas
│   ├── user.py
│   ├── equipment.py
│   ├── event.py
│   ├── bag.py
│   ├── transaction.py
│   ├── reservation.py
│   └── audit_log.py
├── repositories/       # Data access layer
│   ├── base.py        # Base repository
│   ├── user_repo.py
│   ├── equipment_repo.py
│   ├── event_repo.py
│   ├── bag_repo.py
│   ├── transaction_repo.py
│   ├── reservation_repo.py
│   └── audit_log_repo.py
├── services/           # Business logic layer
│   ├── auth_service.py
│   ├── user_service.py
│   ├── equipment_service.py
│   ├── event_service.py
│   ├── bag_service.py
│   ├── transaction_service.py
│   ├── reservation_service.py
│   └── report_service.py
├── routes/             # API endpoints
│   ├── auth.py        # Authentication routes
│   ├── users.py      # User management
│   ├── equipment.py  # Equipment CRUD
│   ├── events.py     # Events CRUD
│   ├── bags.py       # Bags CRUD
│   ├── transactions.py # Transaction tracking
│   ├── reservations.py # Reservations CRUD
│   └── reports.py    # Statistics and reports
├── utils/             # Utility functions
│   └── auth.py       # Auth dependencies
├── tests/             # Test suite
│   ├── conftest.py   # Shared fixtures
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
├── enums.py           # Enum definitions
├── requirements.txt   # Python dependencies
├── pyproject.toml     # Ruff configuration
├── pytest.ini         # Pytest configuration
└── api_norte.db      # SQLite database
```

## Data Models

### Equipment
- id, code, name, category
- status: available | reserved | in_use | maintenance | excluded
- condition: excellent | good | fair | poor | damaged
- bag_id, current_event_id, location, description, serial, qr_code

### Bag
- id, code, name, description
- status: available | reserved | in_use | excluded
- current_event_id, is_active

### Event
- id, code, name, type, category
- status: planned | confirmed | in_progress | completed | cancelled
- start_date, end_date, owner_id, location

### Transaction
- id, equipment_id, bag_id, event_id, user_id
- transaction_type: withdrawal | return
- status: pending | confirmed | completed | cancelled
- scheduled_date, actual_date, return_condition

### Reservation
- id, equipment_id, bag_id, event_id, reserved_by
- status: active | completed | cancelled
- start_date, end_date

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
- `GET /equipment/code/{code}` - Get equipment by code
- `POST /equipment/` - Create equipment
- `PUT /equipment/{id}` - Update equipment
- `DELETE /equipment/{id}` - Delete equipment

### Events
- `GET /events/` - List events (with filters)
- `GET /events/{id}` - Get event by ID
- `GET /events/code/{code}` - Get event by code
- `POST /events/` - Create event
- `PUT /events/{id}` - Update event
- `DELETE /events/{id}` - Delete event

### Bags
- `GET /bags/` - List bags
- `GET /bags/{id}` - Get bag by ID
- `GET /bags/code/{code}` - Get bag by code
- `POST /bags/` - Create bag
- `PUT /bags/{id}` - Update bag
- `DELETE /bags/{id}` - Delete bag
- `POST /bags/{id}/equipment/{code}` - Add equipment to bag
- `DELETE /bags/{id}/equipment/{equipmentId}` - Remove equipment from bag

### Transactions
- `GET /transactions/` - List transactions
- `GET /transactions/{id}` - Get transaction by ID
- `POST /transactions/` - Create transaction (withdrawal/return)
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
- `GET /reports/audit-log` - Audit log
- `GET /reports/audit-log/summary` - Audit log summary

## Testing

The project has a comprehensive test suite.

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
- **Authentication** - Login, register, token validation
- **Users** - CRUD operations, profile updates
- **Equipment** - CRUD, status transitions
- **Events** - CRUD, status management
- **Bags** - CRUD, equipment management
- **Transactions** - Withdrawal and return flows
- **Reservations** - Reservation management
- **Reports** - Dashboard and statistics
- **Security** - Authorization, password hashing

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

The frontend uses HTTP-only cookies for security. Include the JWT token in the Authorization header:
```
Authorization: Bearer <your_token>
```

## User Roles

- **admin** - Full access to all features
- **manager** - Manage events, reservations, transactions
- **operator** - Record withdrawals and returns
- **viewer** - Read-only access

## Admin Access

Default admin user: `lucas` / `admin`

## Architecture

The project follows a layered architecture:

```
Routes → Services → Repositories → Models
         ↓
      Schemas (validation)
```

- **Models** - Database entities (SQLAlchemy)
- **Schemas** - Request/response validation (Pydantic)
- **Repositories** - Data access layer
- **Services** - Business logic
- **Routes** - API endpoints

## Notes

- Requires `bcrypt==4.0.1` (passlib compatibility)
- Test database uses `/tmp/test_api_norte.db`
- Database uses string UUIDs for compatibility
- All enums use lowercase values in the database
