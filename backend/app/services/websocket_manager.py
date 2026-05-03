from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import json
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections for real-time updates.
    
    Handles:
    - Connection tracking
    - Broadcasting events to all connected clients
    - Per-agent filtered updates
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.agent_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        """Register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                await self.disconnect(connection)

    async def send_to_agent(self, agent_id: str, message: dict):
        """Send message to specific agent"""
        if agent_id in self.agent_connections:
            for connection in self.agent_connections[agent_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to agent: {e}")

    async def register_agent(self, agent_id: str, websocket: WebSocket):
        """Register agent for targeted updates"""
        if agent_id not in self.agent_connections:
            self.agent_connections[agent_id] = set()
        self.agent_connections[agent_id].add(websocket)
        logger.info(f"Agent {agent_id} connected for real-time updates")

    async def unregister_agent(self, agent_id: str, websocket: WebSocket):
        """Unregister agent"""
        if agent_id in self.agent_connections:
            self.agent_connections[agent_id].discard(websocket)
            if not self.agent_connections[agent_id]:
                del self.agent_connections[agent_id]
        logger.info(f"Agent {agent_id} disconnected from real-time updates")
