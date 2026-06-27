from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from api.database import SessionLocal, engine
from api.mqtt import start_mqtt_listener
from api.models import AccessLog, Base, User
from api.routes.rfid import router as rfid_router
import api.websocket_manager as ws

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RFID API")

# CORS for ESP32/dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(rfid_router)

# Start MQTT listener as background task
mqtt_client = start_mqtt_listener()


@app.on_event("startup")
def on_startup():
    """Start MQTT listener on startup."""
    # Capture the main asyncio loop for WebSocket broadcasts
    ws.main_loop = asyncio.get_event_loop()
    mqtt_client.loop_start()


@app.on_event("shutdown")
def on_shutdown():
    """Stop MQTT listener on shutdown."""
    mqtt_client.loop_stop()



@app.get("/")
def home():
    return {"status": "API ONLINE"}


@app.get("/health")
def health():
    return {"service": "ok"}


@app.get("/logs")
def list_logs(
    uid: str | None = None,
    limit: int = 100,
    offset: int = 0,
):
    """List RFID access logs, optionally filtered by uid."""
    db = SessionLocal()
    try:
        query = db.query(AccessLog)
        if uid:
            query = query.filter(AccessLog.uid == uid)
        logs = query.order_by(AccessLog.created_at.desc()).offset(offset).limit(limit).all()
        return [
            {
                "id": log.id,
                "uid": log.uid,
                "status": log.status,
                "rssi": log.rssi,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ]
    finally:
        db.close()