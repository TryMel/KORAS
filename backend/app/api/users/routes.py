from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models.models import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    vulnerable_mode: Optional[bool] = None

class UserProfileResponse(BaseModel):
    id: str
    phone: str
    display_name: Optional[str]
    locale: str
    timezone: str
    status: str
    role: str
    vulnerable_mode: bool

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    return UserProfileResponse(
        id=current_user.id,
        phone=current_user.phone,
        display_name=current_user.display_name,
        locale=current_user.locale,
        timezone=current_user.timezone,
        status=current_user.status,
        role=current_user.role,
        vulnerable_mode=current_user.vulnerable_mode
    )

@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if req.display_name is not None:
        current_user.display_name = req.display_name
    if req.locale is not None:
        current_user.locale = req.locale
    if req.timezone is not None:
        current_user.timezone = req.timezone
    if req.vulnerable_mode is not None:
        # Section 62 - Mode utilisateur vulnérable
        current_user.vulnerable_mode = req.vulnerable_mode

    await db.commit()
    await db.refresh(current_user)

    return UserProfileResponse(
        id=current_user.id,
        phone=current_user.phone,
        display_name=current_user.display_name,
        locale=current_user.locale,
        timezone=current_user.timezone,
        status=current_user.status,
        role=current_user.role,
        vulnerable_mode=current_user.vulnerable_mode
    )

@router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Section 75 - Droit à la suppression des données."""
    await db.delete(current_user)
    await db.commit()
    return {"message": "Compte et toutes les données associées supprimés définitivement."}
