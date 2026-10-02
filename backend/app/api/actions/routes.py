from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models.models import Transaction, AuditLog, User
from app.core.dependencies import get_current_user
from app.core.security import generate_idempotency_key
from app.agent.agent_runtime import AgentRuntime
from app.core.logging import logger

router = APIRouter(prefix="/transactions", tags=["Transactions"])

class TransactionPreviewRequest(BaseModel):
    amount: float
    currency: str = "XOF"
    recipient: str
    provider: str = "wave"
    context: Optional[Dict[str, Any]] = None

class TransactionPreviewResponse(BaseModel):
    transaction_id: Optional[str] = None
    idempotency_key: str
    amount: float
    currency: str
    recipient: str
    provider: str
    estimated_fee: float = 0.0
    total_amount: float
    risk_level: int = 4
    requires_biometric: bool = True
    preview_message: str
    status: str = "preview"

@router.post("/preview", response_model=TransactionPreviewResponse)
async def preview_transaction(
    req: TransactionPreviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Section 19 - Génère un aperçu de la transaction avant toute exécution.
    Aucun fonds n'est déplacé à cette étape.
    """
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Le montant doit être positif.")
    if not req.recipient.strip():
        raise HTTPException(status_code=400, detail="Destinataire requis.")

    # Estimated fee (provider-dependent, simplified here)
    fee_rate = 0.01 if req.provider in ["wave", "orange_money"] else 0.02
    fee = round(req.amount * fee_rate, 2)
    total = req.amount + fee
    idemp_key = generate_idempotency_key()

    preview_msg = (
        f"Vous allez envoyer {req.amount:,.0f} {req.currency} "
        f"à {req.recipient} via {req.provider.replace('_', ' ').title()}. "
        f"Frais estimés : {fee:,.0f} {req.currency}. "
        f"Total débité : {total:,.0f} {req.currency}."
    )

    logger.info(f"Transaction preview generated for user={current_user.id}, amount={req.amount}, recipient={req.recipient}")

    return TransactionPreviewResponse(
        idempotency_key=idemp_key,
        amount=req.amount,
        currency=req.currency,
        recipient=req.recipient,
        provider=req.provider,
        estimated_fee=fee,
        total_amount=total,
        preview_message=preview_msg,
        status="preview"
    )

@router.post("/{idempotency_key}/confirm")
async def confirm_transaction(
    idempotency_key: str,
    biometric_authenticated: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Section 19 - Confirmation explicite après vérification biométrique.
    Vérifie idempotence avant exécution (Section 20).
    """
    # Check idempotency - never re-execute an existing transaction
    res = await db.execute(
        select(Transaction).where(Transaction.idempotency_key == idempotency_key)
    )
    existing_tx = res.scalars().first()
    if existing_tx:
        return {
            "message": "Transaction déjà traitée (idempotence).",
            "transaction_id": existing_tx.id,
            "status": existing_tx.status,
            "provider_reference": existing_tx.provider_reference
        }

    if not biometric_authenticated:
        raise HTTPException(
            status_code=403,
            detail="Authentification biométrique obligatoire pour confirmer un transfert d'argent."
        )

    return {
        "message": "Transfert en cours d'exécution. Veuillez patienter.",
        "idempotency_key": idempotency_key,
        "status": "EXECUTING"
    }

@router.get("/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    tx = res.scalars().first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction introuvable.")

    return {
        "id": tx.id,
        "provider": tx.provider,
        "amount": tx.amount,
        "currency": tx.currency,
        "recipient": tx.recipient,
        "idempotency_key": tx.idempotency_key,
        "status": tx.status,
        "provider_reference": tx.provider_reference,
        "created_at": str(tx.created_at),
        "updated_at": str(tx.updated_at)
    }
