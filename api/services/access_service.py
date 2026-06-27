import json
import logging
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from api.config import MQTT_RESPONSE_TOPIC
from api.models import AccessLog, User
from api.websocket_manager import manager as ws_manager
import api.websocket_manager as ws
import api.mqtt as mqtt_module

logger = logging.getLogger(__name__)

def verify_and_log_access(db: Session, uid: str, rssi: float | None = None) -> dict:
    """
    Checks if the RFID UID is authorized, logs the result to the database,
    sends WebSocket updates to dashboard clients, and posts MQTT responses to the ESP32.
    """
    uid = uid.strip().upper()
    
    # 1. Look up user by RFID tag
    user = db.query(User).filter(User.rfid_uuid == uid).first()
    
    if not user:
        status = "denied"
        reason = "unregistered"
        username = "Unknown Tag"
    elif not user.active:
        status = "denied"
        reason = "inactive"
        username = user.name
    else:
        status = "authorized"
        reason = "success"
        username = user.name

    # 2. Create access log entry
    access_log = AccessLog(
        uid=uid,
        status=status,
        rssi=rssi,
        created_at=datetime.utcnow()
    )
    
    try:
        db.add(access_log)
        db.commit()
        db.refresh(access_log)
        logger.info(f"Registered RFID access: UID={uid}, User='{username}', Status={status} ({reason})")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to commit access log for UID {uid}: {e}")
        # Continue to notify clients even if writing logs to db fails temporarily

    # 3. Construct event payload
    event_data = {
        "id": access_log.id,
        "uid": uid,
        "status": status,
        "reason": reason,
        "username": username,
        "rssi": rssi,
        "created_at": access_log.created_at.isoformat() + "Z"
    }

    # 4. Broadcast live update to all active WebSockets on the main event loop
    if ws.main_loop:
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(event_data),
            ws.main_loop
        )
    else:
        logger.warning("Main event loop reference not available, WebSocket broadcast skipped.")

    # 5. Publish decision back to MQTT for ESP32 feedback
    mqtt_response = {
        "uid": uid,
        "status": status,
        "name": username
    }
    mqtt_module.publish_message(MQTT_RESPONSE_TOPIC, json.dumps(mqtt_response))

    return event_data
