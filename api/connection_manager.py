from typing import Dict, List
from fastapi import WebSocket
import logging
import json

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Manages WebSocket connections for real-time agent perception.
    Handles user-specific channels and broadcasting.
    """
    def __init__(self):
        # Store active connections: {client_id: [WebSocket, ...]}
        # Allowing multiple tabs for same user if needed, or single?
        # Let's assume list of sockets per client_id
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        logger.info(f"🔌 Client {client_id} connected. Active sessions: {len(self.active_connections[client_id])}")

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        logger.info(f"🔌 Client {client_id} disconnected")

    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific user"""
        if client_id in self.active_connections:
            msg_str = json.dumps(message, ensure_ascii=False)
            dead_sockets = []
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_text(msg_str)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to send WS message to {client_id}: {e}")
                    dead_sockets.append(connection)
            
            # Cleanup dead sockets
            for ds in dead_sockets:
                self.disconnect(ds, client_id)

    async def broadcast(self, message: dict):
        """Broadcast to all connected users (Admin Dashboard style)"""
        msg_str = json.dumps(message, ensure_ascii=False)
        for client_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_text(msg_str)
                except:
                    pass

# Global Manager Instance
manager = ConnectionManager()
