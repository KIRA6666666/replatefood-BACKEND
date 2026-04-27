# MealSaver Backend

FastAPI backend for MealSaver — a platform connecting restaurants with customers via discounted unsold meal offers.

This first draft scaffolds the shared `users` model from the architecture doc and JWT-based authentication. Restaurant/customer profiles, offers, and orders will follow.

## Stack

- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (async) + PostgreSQL via asyncpg
- Alembic for migrations
- JWT (python-jose) + bcrypt password hashing (passlib)

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # edit DATABASE_URL and JWT_SECRET_KEY

alembic revision --autogenerate -m "create users table"
alembic upgrade head

uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

## Auth endpoints

| Method | Path                    | Purpose                                                            |
|--------|-------------------------|--------------------------------------------------------------------|
| POST   | `/api/v1/auth/register` | Create a user (`role`: customer / restaurant / admin)              |
| POST   | `/api/v1/auth/login`    | OAuth2 password flow → returns `access_token`                      |
| GET    | `/api/v1/users/me`      | Returns the currently authenticated user (requires Bearer token)   |

The login endpoint follows the OAuth2 password form spec, so the user's email goes in the `username` field.

## Layout

```
app/
  core/        config + JWT/password helpers
  db/          async engine, session, declarative Base
  models/      SQLAlchemy models (User + UserRole enum)
  schemas/     Pydantic request/response models
  crud/        DB access functions
  api/
    deps.py    DbSession, CurrentUser, role guards
    routes/    auth, users
  main.py      FastAPI app factory
alembic/       migration environment
```
