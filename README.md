# Chrono Guide

An intelligent task scheduling system that uses AI to extract tasks from content sources and automatically schedule them based on your availability.

## Features

- **AI Task Extraction**: Extract tasks from images, PDFs, and text using Google Gemini
- **Intelligent Scheduling**: Automatically schedule tasks based on availability, priorities, and deadlines
- **Task Management**: Full CRUD operations with priorities, deadlines, and duration estimates
- **Calendar Export**: Export scheduled tasks as iCalendar files

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, SQLModel, Google Gemini AI
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, ShadCN
- **Infrastructure**: Docker, Docker Compose

## Prerequisites

- Docker & Docker Compose
- Git

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd chrono-guide
   ```

2. **Infrastructure Setup (Critical)**
   You need a root `.env` file to handle Docker permissions and ports.

   **Create a file named `.env` in the root folder:**
   ```env
   UID=1000
   GID=1000
   ```
   
   **For macOS / Windows (Docker Desktop):**
   ```bash
   # Root .env
   UID=0
   GID=0
   ```
   
   **For Linux:**
   ```bash
   # Root .env
   # Run "id -u" and "id -g" to confirm your IDs if needed
   UID=1000
   GID=1000
   ``` 

3. **Backend Secrets Setup**
   Create `backend/.env` for your application keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   JWT_SECRET_KEY=your_secret_key_here
   # CORS_ORIGINS is optional, defaults to localhost
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   ```
4. **Frontend Secrets Setup**
   Create `backend/.env.local` for the API's url:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

5. **Start Development Environment**
   Docker automatically picks up the override file for development.
   ```bash
   docker compose up --build
   ```
   *Note: Database migrations run automatically on startup.*

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Local Development

### Backend
```bash
cd backend
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

### Frontend
```bash
# Development (Auto-uses docker-compose.yml + docker-compose.override.yml)
docker compose up

# Production (Explicitly uses base + prod config)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Stop containers
docker compose down

# Database migrations (Manual run)
docker compose exec api poetry run alembic upgrade head
```

## Project Structure

```
chrono-guide/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # API routes
│   │   ├── core/     # Config, auth, db
│   │   ├── crud/     # Database operations
│   │   ├── models/   # Database models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   │   └── tasks/    # Celery Tasks
│   ├── scripts/      # Startup and utility scripts
│   └── tests/        # Test suite
├── frontend/          # Next.js frontend
│   └── src/
│       ├── app/      # Next.js pages
│       ├── components/
│       └── lib/      # Utilities
└── docker-compose.yml
```

## Environment Variables

### Infrastructure (`/.env`)
Controls Docker behavior.
- `UID`/`GID`: Maps container user to host user (prevents permission errors).

### Backend (`backend/.env`)
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `JWT_SECRET_KEY` - JWT secret key (required)
- `CORS_ORIGINS` - Comma-separated list of allowed frontend origins (optional, defaults to `http://localhost:3000,http://127.0.0.1:3000` for dev)
- `DATABASE_URL` - PostgreSQL connection string (optional in Docker, required for local development)

**Note**: When using Docker Compose, `DATABASE_URL` is automatically configured. You can also override it by setting individual PostgreSQL variables:
- `POSTGRES_USER` (default: `chrono`)
- `POSTGRES_PASSWORD` (default: `chrono`)
- `POSTGRES_HOST` (default: `localhost` for local, `db` for Docker)
- `POSTGRES_PORT` (default: `5432`)
- `POSTGRES_DB` (default: `chrono`)

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Testing

```bash
# Backend tests
docker-compose exec api poetry run pytest

# With coverage
docker-compose exec api poetry run pytest --cov=app
```

## Database Migrations

```bash
# Create migration
docker-compose exec api poetry run alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api poetry run alembic upgrade head
```

## License

Private project - All rights reserved.
