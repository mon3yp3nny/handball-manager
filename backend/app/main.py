from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.session import engine, Base
from app.models import *
from app.core.deps import get_current_user
from app.websocket.manager import manager
from app.core.security import decode_token


# Create database tables
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up Handball Manager API...")
    yield
    # Shutdown
    print("Shutting down Handball Manager API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "message": "Handball Manager API",
        "version": settings.VERSION,
        "docs": "/api/v1/docs",
        "api": "/api/v1"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.VERSION}


# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Wait for authentication
    try:
        auth_message = await websocket.receive_text()
        auth_data = {}
        try:
            import json
            auth_data = json.loads(auth_message)
        except:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
            await websocket.close()
            return
        
        token = auth_data.get("token")
        if not token:
            await websocket.send_text(json.dumps({"type": "error", "message": "No token provided"}))
            await websocket.close()
            return
        
        # Validate token
        payload = decode_token(token)
        if not payload:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid token"}))
            await websocket.close()
            return
        
        user_id = payload.get("sub")
        if not user_id:
            await websocket.send_text(json.dumps({"type": "error", "message": "Invalid token"}))
            await websocket.close()
            return
        
        # Connect the user
        await manager.connect(websocket, user_id)
        await websocket.send_text(json.dumps({"type": "connected", "user_id": user_id}))
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle subscription messages
                if message.get("action") == "subscribe_team":
                    team_id = message.get("team_id")
                    if team_id:
                        manager.subscribe_to_team(user_id, team_id)
                        await websocket.send_text(json.dumps({
                            "type": "subscribed",
                            "team_id": team_id
                        }))
                
                elif message.get("action") == "unsubscribe_team":
                    team_id = message.get("team_id")
                    if team_id:
                        manager.unsubscribe_from_team(user_id, team_id)
                        await websocket.send_text(json.dumps({
                            "type": "unsubscribed",
                            "team_id": team_id
                        }))
                
                elif message.get("action") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "message": "Invalid JSON"}))
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        # Clean up on disconnect
        if 'user_id' in locals():
            manager.disconnect(user_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
