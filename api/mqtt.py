"""MQTT listener for receiving RFID tag data from ESP32 devices."""

import json
import logging
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session

from api.config import MQTT_HOST, MQTT_PORT, MQTT_TOPIC
from api.database import SessionLocal

logger = logging.getLogger(__name__)

# Keep a reference to the active MQTT client instance to publish responses back to the ESP32.
_client = None

def on_connect(client, userdata, flags, rc):
    """Callback when MQTT connection is established."""
    logger.info("MQTT connected, subscribing to '%s'", MQTT_TOPIC)
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    """Handle incoming MQTT messages from ESP32 devices."""
    try:
        payload = json.loads(msg.payload.decode())

        uid = str(payload.get("uid", ""))
        rssi = payload.get("rssi")

        if not uid:
            logger.warning("Received MQTT message without uid: %s", msg.payload)
            return

        # Process access verification
        db: Session = SessionLocal()
        try:
            from api.services.access_service import verify_and_log_access
            verify_and_log_access(db, uid, rssi)
        except Exception:
            logger.exception("Failed to process RFID access via MQTT")
        finally:
            db.close()

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.error("Error parsing MQTT message: %s", e)


def start_mqtt_listener():
    """Create and return an MQTT client connected to the broker."""
    global _client
    _client = mqtt.Client()
    _client.on_connect = on_connect
    _client.on_message = on_message
    try:
        # Use connect_async to prevent API crash on startup when the broker is offline
        _client.connect_async(MQTT_HOST, MQTT_PORT, 60)
        logger.info("Initialized MQTT client connection (async to %s:%d)", MQTT_HOST, MQTT_PORT)
    except Exception as e:
        logger.error("Failed to initialize async MQTT connection: %s", e)
    return _client


def publish_message(topic: str, payload: str):
    """Publish an MQTT message to the broker (used to send responses back to ESP32)."""
    global _client
    if _client:
        try:
            _client.publish(topic, payload)
            logger.info("Published to MQTT topic '%s': %s", topic, payload)
        except Exception as e:
            logger.error("Failed to publish MQTT message to topic '%s': %s", topic, e)
    else:
        logger.warning("MQTT client not initialized, cannot publish message to topic '%s'", topic)

