from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from api.database import SessionLocal
from api.models import User, AccessLog
from api.websocket_manager import manager
from api.services.access_service import verify_and_log_access

router = APIRouter()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class UserCreate(BaseModel):
    name: str
    rfid_uuid: str
    email: Optional[str] = None
    apartment: Optional[str] = None
    role: str = "user"
    active: bool = True

class AccessSimulate(BaseModel):
    uid: str
    rssi: Optional[float] = None

# --- WebSocket Endpoints ---
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for dashboard clients to receive live RFID scans."""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, listen for any messages (none expected currently)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- User Management Endpoints ---
@router.post("/users", response_model=dict)
def create_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Create a new user and map their RFID tag."""
    uid_upper = user_in.rfid_uuid.strip().upper()
    
    # Check if RFID UUID is already registered
    existing_user = db.query(User).filter(User.rfid_uuid == uid_upper).first()
    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail=f"RFID tag '{uid_upper}' is already registered to user '{existing_user.name}'"
        )
    
    user = User(
        name=user_in.name,
        rfid_uuid=uid_upper,
        email=user_in.email,
        apartment=user_in.apartment,
        role=user_in.role,
        active=user_in.active
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return {
            "id": user.id,
            "name": user.name,
            "rfid_uuid": user.rfid_uuid,
            "email": user.email,
            "apartment": user.apartment,
            "role": user.role,
            "active": user.active
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    """List all registered users."""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "rfid_uuid": u.rfid_uuid,
            "email": u.email,
            "apartment": u.apartment,
            "role": u.role,
            "active": u.active
        }
        for u in users
    ]

@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a registered user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        db.delete(user)
        db.commit()
        return {"status": "success", "message": f"User '{user.name}' has been deleted."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.post("/users/{user_id}/toggle-active")
def toggle_user_active(user_id: int, db: Session = Depends(get_db)):
    """Toggle a user's active status."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        user.active = not user.active
        db.commit()
        db.refresh(user)
        return {
            "id": user.id,
            "name": user.name,
            "active": user.active
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

# --- RFID Simulation Endpoint ---
@router.post("/rfid/access-test")
def simulate_rfid_access(payload: AccessSimulate, db: Session = Depends(get_db)):
    """Simulates an RFID tag swipe (HTTP-based test endpoint)."""
    return verify_and_log_access(db, payload.uid, payload.rssi)
