import asyncio
import json
import logging
from typing import Dict, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # active_connections: {user_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # team_subscriptions: {team_id: set(user_ids)}
        self.team_subscriptions: Dict[int, Set[int]] = {}
        # The app's running event loop, captured at startup so sync request
        # handlers (which run in a threadpool) can schedule broadcasts onto
        # it via run_coroutine_threadsafe.
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, websocket: WebSocket, user_id: int):
        # The endpoint already accepted the handshake (it must, to read the
        # auth cookie and send auth errors), so we only register here.
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
                    except (ConnectionError, RuntimeError) as exc:
                        logger.warning(
                            "Failed to send to user_id=%s on team_id=%s: %s",
                            user_id, team_id, exc,
                        )
                        disconnected.append(user_id)

            # Clean up disconnected users
            for user_id in disconnected:
                self.disconnect(user_id)

    async def broadcast(self, message: dict):
        """Broadcast to all connected clients"""
        disconnected = []
        # Snapshot first: send_text awaits, and a disconnect cleanup during
        # iteration would mutate active_connections mid-loop.
        for user_id, connection in list(self.active_connections.items()):
            try:
                await connection.send_text(json.dumps(message))
            except (ConnectionError, RuntimeError) as exc:
                logger.warning("Broadcast failed for user_id=%s: %s", user_id, exc)
                disconnected.append(user_id)

        # Clean up disconnected users
        for user_id in disconnected:
            self.disconnect(user_id)

    def notify(self, message: dict) -> None:
        """Fire-and-forget broadcast schedulable from sync code.

        Request handlers run in a threadpool with no running loop, so we
        hand the coroutine to the captured app loop. No-op before startup
        binds the loop (e.g. under unit tests with no live server).
        """
        if self._loop is None:
            return
        try:
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)
        except RuntimeError as exc:
            logger.warning("notify scheduling failed: %s", exc)


# Global connection manager instance
manager = ConnectionManager()


def notify_resource(resource: str, action: str) -> None:
    """Tell every connected client that a resource changed so they can
    invalidate their cached queries. Carries no row data — the client's
    refetch goes through the REST API, which enforces per-user RBAC."""
    manager.notify({"type": "resource_changed", "resource": resource, "action": action})
