from typing import List, Dict, Set
from fastapi import WebSocket
import json
import asyncio


class ConnectionManager:
    def __init__(self):
        # active_connections: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # team_subscriptions: {team_id: set(user_ids)}
        self.team_subscriptions: Dict[int, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove from all team subscriptions
        for team_id, users in self.team_subscriptions.items():
            users.discard(user_id)
    
    def subscribe_to_team(self, user_id: int, team_id: int):
        if team_id not in self.team_subscriptions:
            self.team_subscriptions[team_id] = set()
        self.team_subscriptions[team_id].add(user_id)
    
    def unsubscribe_from_team(self, user_id: int, team_id: int):
        if team_id in self.team_subscriptions:
            self.team_subscriptions[team_id].discard(user_id)
    
    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))
    
    async def broadcast_to_team(self, message: dict, team_id: int):
        if team_id in self.team_subscriptions:
            disconnected = []
            for user_id in self.team_subscriptions[team_id]:
                if user_id in self.active_connections:
                    try:
                        await self.active_connections[user_id].send_text(json.dumps(message))
                    except:
                        disconnected.append(user_id)
            
            # Clean up disconnected users
            for user_id in disconnected:
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        disconnected = []
        for user_id, connection in self.active_connections.items():
            try:
                await connection.send_text(json.dumps(message))
            except:
                disconnected.append(user_id)
        
        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(user_id)


# Global connection manager instance
manager = ConnectionManager()
