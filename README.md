# Handball Manager

A comprehensive handball club management application for managing teams, players, games, and events.

## Features

### Core Features
- 👥 **User Management** - Role-based access control (Admin, Coach, Supervisor, Player, Parent)
- 🏆 **Team Management** - Create teams, assign players and coaches
- 👤 **Player Profiles** - Contact info, positions, statistics
- 🎮 **Game Scheduling** - Schedule games with opponents, locations, and results
- 📅 **Event Calendar** - Training, meetings, tournaments
- ✅ **Attendance Tracking** - Track attendance for games and events
- 📰 **News/Announcements** - Team-specific and global news
- 👨‍👩‍👧 **Parent-Child Linking** - Parents see their children's schedules

### Technical Features
- 🔐 JWT Authentication with refresh tokens
- 🌐 REST API with comprehensive documentation (OpenAPI/Swagger)
- 🔄 Real-time updates via WebSocket
- 📱 Responsive design (mobile-first)
- 🐳 Docker Compose for easy deployment

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with role-based access control
- **WebSocket**: For real-time updates
- **API Documentation**: OpenAPI/Swagger

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Build Tool**: Vite

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Docker Compose Setup

```bash
# Clone the repository
cd handball-manager

# Build and run with docker-compose
docker-compose up --build

# Access the application
# Frontend: http://localhost
# Backend API: http://localhost:8000/api/v1
# API Documentation: http://localhost:8000/api/v1/docs
```

### Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the server
uvicorn app.main:app --reload --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# The app will be available at http://localhost:3000
```

## Project Structure

```
handball-manager/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Config, security, dependencies
│   │   ├── db/             # Database session
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   └── websocket/      # WebSocket manager
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                # React application
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── store/          # State management
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── mobile/                  # Future mobile apps (placeholder)
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PUT /api/v1/users/{id}` - Update user

### Teams
- `GET /api/v1/teams` - List teams
- `POST /api/v1/teams` - Create team
- `GET /api/v1/teams/{id}` - Get team
- `PUT /api/v1/teams/{id}` - Update team
- `DELETE /api/v1/teams/{id}` - Delete team

### Players
- `GET /api/v1/players` - List players
- `POST /api/v1/players` - Create player
- `GET /api/v1/players/{id}` - Get player
- `PUT /api/v1/players/{id}` - Update player

### Games
- `GET /api/v1/games` - List games
- `POST /api/v1/games` - Create game
- `GET /api/v1/games/{id}` - Get game
- `PUT /api/v1/games/{id}` - Update game
- `PATCH /api/v1/games/{id}/result` - Update game result

### Events
- `GET /api/v1/events` - List events
- `POST /api/v1/events` - Create event
- `GET /api/v1/events/{id}` - Get event
- `PUT /api/v1/events/{id}` - Update event

### Attendance
- `GET /api/v1/attendance` - List attendance records
- `POST /api/v1/attendance` - Create attendance record
- `PUT /api/v1/attendance/{id}` - Update attendance status
- `POST /api/v1/attendance/bulk-update` - Bulk update attendance

### News
- `GET /api/v1/news` - List news
- `POST /api/v1/news` - Create news
- `GET /api/v1/news/{id}` - Get news
- `PUT /api/v1/news/{id}` - Update news
- `PATCH /api/v1/news/{id}/publish` - Publish/unpublish news

## Roles and Permissions

| Feature | Admin | Coach | Supervisor | Player | Parent |
|---------|-------|-------|------------|--------|--------|
| View Teams | ✅ | ✅ | ✅ | ✅* | ✅* |
| Manage Teams | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Players | ✅ | ✅ | ✅ | ✅* | ✅* |
| Manage Players | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Games | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage Games | ✅ | ✅ | ❌ | ❌ | ❌ |
| Update Game Results | ✅ | ✅ | ✅ | ❌ | ❌ |
| View Events | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage Events | ✅ | ✅ | ✅ | ❌ | ❌ |
| Mark Attendance | ✅ | ✅ | ✅ | ✅* | ✅* |
| View News | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage News | ✅ | ✅ | ✅ | ❌ | ❌ |

*Restricted to own/relevant data

## WebSocket

WebSocket endpoint: `ws://localhost:8000/ws`

Authentication message:
```json
{
  "token": "<JWT_TOKEN>"
}
```

Subscribe to team updates:
```json
{
  "action": "subscribe_team",
  "team_id": 1
}
```

## Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@handball.de | admin123 |
| Coach | coach@handball.de | coach123 |

## Development

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm run test
```

### Database Migrations (using Alembic)

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Production Build

```bash
# Build and run
docker-compose -f docker-compose.prod.yml up --build -d
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Support

For support, please open an issue on GitHub or contact the development team.
