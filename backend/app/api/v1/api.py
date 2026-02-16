from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, teams, players, games, events, attendance, news, parents

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(teams.router, prefix="/teams", tags=["Teams"])
api_router.include_router(players.router, prefix="/players", tags=["Players"])
api_router.include_router(games.router, prefix="/games", tags=["Games"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["Attendance"])
api_router.include_router(news.router, prefix="/news", tags=["News"])
api_router.include_router(parents.router, prefix="/parents", tags=["Parents"])
