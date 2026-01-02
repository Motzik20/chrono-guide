# Chrono Guide

An intelligent task scheduling system that uses AI to extract tasks from content sources and automatically schedule them based on your availability.

## Features

- **AI Task Extraction**: Extract tasks from images, PDFs, and text using Google Gemini
- **Intelligent Scheduling**: Automatically schedule tasks based on availability, priorities, and deadlines
- **Task Management**: Full CRUD operations with priorities, deadlines, and duration estimates
- **Calendar Export**: Export scheduled tasks as iCalendar files

## Tech Stack

- **Backend**: FastAPI, PostgreSQL, SQLModel, Google Gemini AI
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, Radix UI
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

2. **Set up backend environment**
   
   Create `backend/.env`:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   JWT_SECRET_KEY=your_secret_key_here
   DATABASE_URL=postgresql+psycopg://chrono:chrono@db:5432/chrono
   ```

3. **Start development environment**
   ```bash
   docker-compose --profile dev up --build
   ```

4. **Access the application**
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
cd frontend
pnpm install
# Create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm dev
```

## Docker Commands

```bash
# Development
docker-compose --profile dev up

# Production
NEXT_PUBLIC_API_URL=http://localhost:8000 docker-compose --profile prod up --build

# Database migrations
docker-compose exec api-dev poetry run alembic upgrade head
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
│   └── tests/        # Test suite
├── frontend/          # Next.js frontend
│   └── src/
│       ├── app/      # Next.js pages
│       ├── components/
│       └── lib/      # Utilities
└── docker-compose.yml
```

## Environment Variables

### Backend (`backend/.env`)
- `GEMINI_API_KEY` - Google Gemini API key (required)
- `SECRET_KEY` - JWT secret key (required)
- `DATABASE_URL` - PostgreSQL connection string (required)

### Frontend (`frontend/.env.local`)
- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)

## Testing

```bash
# Backend tests
docker-compose exec api-dev poetry run pytest

# With coverage
docker-compose exec api-dev poetry run pytest --cov=app
```

## Database Migrations

```bash
# Create migration
docker-compose exec api-dev poetry run alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec api-dev poetry run alembic upgrade head
```

## License

Private project - All rights reserved.
