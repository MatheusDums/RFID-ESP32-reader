import os
from pathlib import Path
from dotenv import load_dotenv

# Caminho absoluto do .env
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# Carregar .env explicitamente
load_dotenv(dotenv_path=ENV_FILE, override=True)

print("ENV FILE:", ENV_FILE)
print("APP_PORT:", os.getenv("APP_PORT"))

APP_NAME = os.getenv("APP_NAME")
APP_HOST = os.getenv("APP_HOST")
APP_PORT = int(os.getenv("APP_PORT", 8000))

MQTT_HOST = os.getenv("MQTT_HOST")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///db_rfid")