from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models.models import User, Device, Session
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.logging import logger

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    phone: str
    display_name: str
    password: str
    device_identifier: str
    android_version: Optional[str] = "14"

class LoginRequest(BaseModel):
    phone: str
    password: str
    device_identifier: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    phone: str
    display_name: Optional[str]
    vulnerable_mode: bool

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    res = await db.execute(select(User).where(User.phone == req.phone))
    existing = res.scalars().first()
    if existing:
        raise HTTPException(status_code=400, detail="Ce numéro de téléphone est déjà enregistré.")

    user = User(
        phone=req.phone,
        display_name=req.display_name,
        hashed_password=get_password_hash(req.password),
        status="active"
    )
    db.add(user)
    await db.flush()

    device = Device(
        user_id=user.id,
        device_identifier=req.device_identifier,
        android_version=req.android_version,
        trust_status="trusted"
    )
    db.add(device)
    await db.flush()
    db.add(Session(user_id=user.id, device_id=device.id, authentication_level="standard"))
    await db.commit()
    await db.refresh(user)

    token = create_access_token({"sub": user.id, "phone": user.phone, "role": user.role})
    logger.info(f"User registered successfully: {user.phone}")
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        phone=user.phone,
        display_name=user.display_name,
        vulnerable_mode=user.vulnerable_mode
    )

@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.phone == req.phone))
    user = res.scalars().first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="Ce compte est suspendu ou inactif.")

    device_id = None
    if req.device_identifier:
        device_res = await db.execute(select(Device).where(
            Device.user_id == user.id, Device.device_identifier == req.device_identifier
        ))
        device = device_res.scalars().first()
        if device and device.trust_status == "trusted":
            device_id = device.id
    db.add(Session(user_id=user.id, device_id=device_id, authentication_level="standard"))
    await db.commit()
    token = create_access_token({"sub": user.id, "phone": user.phone, "role": user.role})
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        phone=user.phone,
        display_name=user.display_name,
        vulnerable_mode=user.vulnerable_mode
    )
