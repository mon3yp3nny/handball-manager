# Handball Manager

A comprehensive handball club management application for managing teams, players, games, and events.

## Features

### Core Features
- 👥 **User Management** - Role-based access control (Admin, Coach, Supervisor, Player, Parent)
- 🔐 **OAuth Authentication** - Apple Sign In (iCloud) & Google Sign In integration
- 🏆 **Team Management** - Create teams, assign players and coaches
- 👤 **Player Profiles** - Contact info, positions, statistics
- 🎮 **Game Scheduling** - Schedule games with opponents, locations, and results
- 📅 **Event Calendar** - Training, meetings, tournaments
- ✅ **Attendance Tracking** - Track attendance for games and events
- 📰 **News/Announcements** - Team-specific and global news
- 👨‍👩‍👧 **Parent-Child Linking** - Parents see their children's schedules (restricted view)
- ✉️ **Invitation System** - Coaches can invite players/parents via email

### Technical Features
- 🔐 JWT + OAuth Authentication with refresh tokens
- 🌐 REST API with comprehensive documentation (OpenAPI/Swagger)
- 🔄 Real-time updates via WebSocket
- 📱 Responsive design (mobile-first)
- 🐳 Docker Compose for easy deployment

## OAuth Authentication

This application supports OAuth sign-in with:
- **Apple Sign In** - Using iCloud authentication
- **Google Sign In** - Using Google accounts

### Setup Requirements

#### Apple Sign In
1. Create an Apple Developer account
2. Configure Sign in with Apple in your Apple Developer Console
3. Set environment variables:
   ```
   APPLE_CLIENT_ID=your.service.id
   ```

#### Google Sign In
1. Create a project in Google Cloud Console
2. Configure OAuth 2.0 credentials
3. Set environment variables:
   ```
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   ```
4. Add your domain to authorized JavaScript origins

### Environment Variables

```bash
# Backend
APPLE_CLIENT_ID=your.apple.service.id
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# Frontend
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens + OAuth (Apple/Google)
- **WebSocket**: For real-time updates
- **API Documentation**: OpenAPI/Swagger

### Frontend
- **Framework**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: TanStack Query
- **Build Tool**: Vite
- **OAuth**: @react-oauth/google, Apple Sign In JS

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)
- Apple Developer account (for Apple Sign In)
- Google Cloud project (for Google Sign In)

### Docker Compose Setup

```bash
# Clone the repository
cd handball-manager

# Set environment variables (create .env file)
cp .env.example .env
# Edit .env with your OAuth credentials

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
│   │   ├── core/           # Config, security, dependencies, OAuth
│   │   ├── db/             # Database session
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic (OAuth, Email)
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

### OAuth
- `POST /api/v1/oauth/google` - Google OAuth login/registration
- `POST /api/v1/oauth/apple` - Apple OAuth login/registration
- `POST /api/v1/oauth/set-role` - Set role for new OAuth users

### Invitations
- `POST /api/v1/invitations/send` - Send invitation
- `GET /api/v1/invitations/sent` - List sent invitations
- `GET /api/v1/invitations/verify/{token}` - Verify invitation
- `POST /api/v1/invitations/resend/{id}` - Resend invitation
- `DELETE /api/v1/invitations/{id}` - Revoke invitation

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
- `POST /api/v1/players` - Create player (with parent linking)
- `GET /api/v1/players/{id}` - Get player
- `PUT /api/v1/players/{id}` - Update player

### Parents
- `GET /api/v1/parents/children` - Get my children (for parents)
- `POST /api/v1/parents/children/{player_id}` - Link child
- `DELETE /api/v1/parents/children/{player_id}` - Unlink child

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
| Send Invitations | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Invitations | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Own Children | ❌ | ❌ | ❌ | ❌ | ✅ |

*Restricted to own/relevant data. Parents only see their own children's profiles and team schedules.

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
| Parent | eltern@handball.de | parent123 |

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

## GitHub Issues & Features

All features are tracked in GitHub Issues:
- [GitHub Issues](https://github.com/mon3yp3nny/handball-manager/issues)

Priority 1 (Critical) - ✅ Implemented:
- Apple Sign In OAuth
- Google Sign In OAuth
- Parent restricted view
- Coach invitation system
- Player creation with parent linking

Priority 2-4 features are tracked as separate issues.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please see CONTRIBUTING.md for guidelines.

## Support

For support, please open an issue on GitHub.
