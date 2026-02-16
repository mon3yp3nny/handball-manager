# Backend

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py
│   │       │   ├── teams.py
│   │       │   ├── players.py
│   │       │   ├── games.py
│   │       │   ├── events.py
│   │       │   ├── attendance.py
│   │       │   └── news.py
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── deps.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── player.py
│   │   ├── game.py
│   │   ├── event.py
│   │   ├── attendance.py
│   │   └── news.py
│   ├── schemas/
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── player.py
│   │   ├── game.py
│   │   ├── event.py
│   │   ├── attendance.py
│   │   └── news.py
│   ├── websocket/
│   │   └── manager.py
│   └── main.py
├── alembic/
├── tests/
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with role-based access control
- **WebSocket**: For real-time updates
- **API Documentation**: OpenAPI/Swagger

## Features

1. User authentication and role management
2. Team management
3. Player profiles
4. Game scheduling
5. Event/appointment calendar
6. Attendance tracking
7. News/announcements
8. Parent-child linking

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
