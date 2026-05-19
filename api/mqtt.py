"""MQTT listener for receiving RFID tag data from ESP32 devices."""

import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from api.config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC
from api.database import SessionLocal
from api.models import AccessLog

logger = logging.getLogger(__name__)


def on_connect(client, userdata, flags, rc):
    """Callback when MQTT connection is established."""
    logger.info("MQTT connected, subscribing to '%s'", MQTT_TOPIC)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    """Handle incoming MQTT messages from ESP32 devices."""
    try:
        payload = json.loads(msg.payload.decode())

        uid = str(payload.get("uid", ""))
        status = str(payload.get("status", "ok"))
        rssi = payload.get("rssi")
        timestamp = payload.get("timestamp")

        if not uid:
            logger.warning("Received MQTT message without uid: %s", msg.payload)
            return

        # Parse timestamp or use current UTC time
        if timestamp:
            created_at = datetime.fromisoformat(timestamp)
        else:
            created_at = datetime.now(timezone.utc)

        # Insert into database
        db: Session = SessionLocal()
        try:
            log = AccessLog(
                uid=uid,
                status=status,
                rssi=rssi,
                created_at=created_at,
            )
            db.add(log)
            db.commit()
            logger.info("Stored RFID log: uid=%s, status=%s", uid, status)
        except Exception:
            db.rollback()
            logger.exception("Failed to store RFID log")
        finally:
            db.close()

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error("Error parsing MQTT message: %s", e)


def start_mqtt_listener():
    """Create and return an MQTT client connected to the broker."""
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    return client
