from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from datetime import datetime

from api.database import Base


class AccessLog(Base):
    __tablename__ = "access_logs"

    id = Column(Integer, primary_key=True, index=True)
    uid = Column(String, nullable=False)
    status = Column(String, nullable=False)
    rssi = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, unique=True)
    apartment = Column(String, nullable=True)
    rfid_uuid = Column(String, nullable=True, unique=True)
    photo = Column(String, nullable=True)
    role = Column(String, nullable=False, default="user")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)