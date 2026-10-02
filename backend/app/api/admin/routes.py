from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database.session import get_db
from app.database.models.models import User, Device, AuditLog, Transaction
from app.core.dependencies import get_current_admin
from app.agent.agent_runtime import AgentRuntime, AgentRunOutput

router = APIRouter(prefix="/admin", tags=["Admin Portal"])

class SimulationRequest(BaseModel):
    simulated_query: str
    vulnerable_user: bool = False
    device_trusted: bool = True
    battery_level: int = 80
    is_offline: bool = False

@router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(User).offset(skip).limit(limit))
    users = res.scalars().all()
    return [{"id": u.id, "phone": u.phone, "display_name": u.display_name, "status": u.status, "role": u.role} for u in users]

@router.get("/devices")
async def get_all_devices(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Device).offset(skip).limit(limit))
    devices = res.scalars().all()
    return [{
        "id": d.id, "user_id": d.user_id, "device_identifier": d.device_identifier,
        "platform": d.platform, "trust_status": d.trust_status, "last_seen_at": str(d.last_seen_at)
    } for d in devices]

@router.get("/audit")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).offset(skip).limit(limit))
    logs = res.scalars().all()
    return [{
        "id": l.id,
        "user_id": l.user_id,
        "actor_type": l.actor_type,
        "event_type": l.event_type,
        "resource_type": l.resource_type,
        "resource_id": l.resource_id,
        "metadata": l.metadata_json,
        "created_at": str(l.created_at)
    } for l in logs]

@router.get("/transactions")
async def get_transactions(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Transaction).order_by(desc(Transaction.created_at)).offset(skip).limit(limit))
    txs = res.scalars().all()
    return [{
        "id": t.id,
        "action_id": t.action_id,
        "provider": t.provider,
        "amount": t.amount,
        "currency": t.currency,
        "recipient": t.recipient,
        "idempotency_key": t.idempotency_key,
        "status": t.status,
        "provider_ref": t.provider_reference,
        "created_at": str(t.created_at)
    } for t in txs]

@router.post("/simulation/run", response_model=AgentRunOutput)
async def simulate_agent(req: SimulationRequest):
    """
    Section 69: Admin simulation environment.
    Runs simulated intent, planning, risk, and tool execution in a completely isolated sandbox.
    """
    sim_output = AgentRuntime.process_request(
        user_input=req.simulated_query,
        context={
            "battery_level": req.battery_level,
            "is_offline": req.is_offline,
            "is_simulation": True
        },
        user_vulnerable_mode=req.vulnerable_user,
        device_trusted=req.device_trusted
    )
    return sim_output
