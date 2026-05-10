from fastapi import FastAPI

from api.database import engine
from api.models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="RFID API"
)


@app.get("/")
def home():

    return {
        "status": "API ONLINE"
    }


@app.get("/health")
def health():

    return {
        "service": "ok"
    }