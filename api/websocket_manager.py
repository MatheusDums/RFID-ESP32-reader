import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Reference to the main FastAPI asyncio event loop, set during application startup.
# This allows background threads (like the MQTT listener thread) to schedule thread-safe broadcasts.
main_loop = None

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Active connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        if not self.active_connections:
            return
        
        logger.info(f"Broadcasting message to {len(self.active_connections)} WebSocket client(s): {message}")
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending JSON payload to WebSocket client: {e}")
                disconnected.append(connection)
                
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()
