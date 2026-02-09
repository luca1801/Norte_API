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
│   └── transaction.py
├── schemas/            # Pydantic schemas
│   ├── user.py
│   ├── equipment.py
│   ├── event.py
│   └── transaction.py
├── routes/             # API endpoints
│   ├── auth.py         # Authentication routes
│   ├── users.py        # User management
│   ├── equipment.py    # Equipment CRUD
│   ├── events.py       # Events CRUD
│   ├── transactions.py # Transaction tracking
│   └── reports.py      # Statistics and reports
├── utils/              # Utility functions
│   └── auth.py         # Auth dependencies
├── main.py             # FastAPI application
└── requirements.txt    # Python dependencies
```

## Setup

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
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

### Transactions
- `GET /transactions/` - List transactions
- `GET /transactions/{id}` - Get transaction by ID
- `POST /transactions/` - Create transaction
- `PUT /transactions/{id}` - Update transaction
- `DELETE /transactions/{id}` - Delete transaction

### Reports
- `GET /reports/dashboard` - Dashboard statistics
- `GET /reports/equipment-usage` - Equipment usage report

## Development

### Linting
```bash
ruff check .
ruff format .
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

Create an admin user by setting `role: "admin"` during registration.
