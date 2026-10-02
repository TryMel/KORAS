from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database.session import get_db
from app.database.models.models import (
    User, Device, Conversation, Message, Intent, AgentRun, Action, Approval, AuditLog, Transaction
)
from app.core.dependencies import get_current_user_optional
from app.agent.agent_runtime import AgentRuntime, AgentRunOutput, PlannedStep, AgentState
from app.core.security import sanitize_untrusted_input
from app.core.logging import logger

router = APIRouter(prefix="/agent", tags=["Agent Execution"])

class AgentRunRequest(BaseModel):
    user_input: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    device_identifier: Optional[str] = None

class ConfirmStepRequest(BaseModel):
    step_id: str
    biometric_authenticated: bool = False
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class StepResultRequest(BaseModel):
    """Observation returned by the trusted Android client after a tool call."""
    status: str = Field(pattern="^(verified|failed|unknown)$")
    result: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None

# In-memory active runs registry for fast multi-turn confirmation & step execution
active_runs_store: Dict[str, Dict[str, Any]] = {}

@router.post("/run", response_model=AgentRunOutput)
async def run_agent(
    req: AgentRunRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    # Sanitize input (Section 25 anti-prompt injection)
    safe_input = sanitize_untrusted_input(req.user_input)

    # Determine user vulnerability status and device trust
    vulnerable_mode = current_user.vulnerable_mode if current_user else False
    user_id = current_user.id if current_user else None

    # A claimed device id is not automatically trusted. Sensitive policy uses
    # the registered device status belonging to the authenticated user.
    device_trusted = False
    if current_user and req.device_identifier:
        device_res = await db.execute(select(Device).where(
            Device.user_id == current_user.id,
            Device.device_identifier == req.device_identifier,
        ))
        device = device_res.scalars().first()
        device_trusted = device is not None and device.trust_status == "trusted"

    # Merge context
    ctx = req.context or {}
    ctx["user_id"] = user_id

    # Execute Agent State Machine
    run_output = AgentRuntime.process_request(
        user_input=safe_input,
        context=ctx,
        user_vulnerable_mode=vulnerable_mode,
        device_trusted=device_trusted
    )

    # Persist the user request and the agent state for the real conversation
    # history. Anonymous sandbox calls remain deliberately non-persistent.
    if current_user:
        conversation = None
        if req.conversation_id:
            conv_res = await db.execute(select(Conversation).where(
                Conversation.id == req.conversation_id, Conversation.user_id == current_user.id
            ))
            conversation = conv_res.scalars().first()
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation introuvable.")
        else:
            conversation = Conversation(user_id=current_user.id, title=safe_input[:80] or "Nouvelle conversation")
            db.add(conversation)
            await db.flush()
        db.add(Message(conversation_id=conversation.id, role="user", content=safe_input, content_type="text", language=ctx["language"]))
        db.add(Message(conversation_id=conversation.id, role="assistant", content=run_output.spoken_response, content_type="text", language=ctx["language"]))

    # Store run state for approval workflow
    active_runs_store[run_output.run_id] = {
        "output": run_output,
        "user_id": user_id,
        "context": ctx,
        "input": safe_input
    }

    # Record Audit Log (Section 68)
    audit = AuditLog(
        user_id=user_id,
        actor_type="user",
        actor_id=user_id,
        event_type="AGENT_RUN_INITIATED",
        resource_type="agent_run",
        resource_id=run_output.run_id,
        metadata_json={
            "input": safe_input,
            "state": run_output.state.value,
            "steps_count": len(run_output.steps)
        }
    )
    db.add(audit)
    await db.commit()

    return run_output

@router.post("/runs/{run_id}/confirm", response_model=AgentRunOutput)
async def confirm_run_step(
    run_id: str,
    req: ConfirmStepRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    run_data = active_runs_store.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Session d'exécution introuvable ou expirée.")

    run_output: AgentRunOutput = run_data["output"]
    if (
        run_output.state != AgentState.WAITING_FOR_CONFIRMATION
        or run_output.awaiting_confirmation_step_id != req.step_id
    ):
        raise HTTPException(status_code=409, detail="Cette étape n'attend pas de confirmation.")
    step = next((s for s in run_output.steps if s.step_id == req.step_id), None)
    if not step:
        raise HTTPException(status_code=404, detail="Étape à confirmer introuvable.")

    # Biometric requirement check
    if step.requires_biometric and not req.biometric_authenticated:
        raise HTTPException(
            status_code=403,
            detail="Authentification biométrique requise pour cette action financière."
        )

    # Confirmation only authorises the client-side action.  It does not execute
    # a device or partner tool from the backend.
    updated_step = AgentRuntime.confirm_and_execute_step(step, req.context)

    # Update state
    run_output.state = AgentState.READY_TO_EXECUTE
    run_output.spoken_response = "Confirmation reçue. Exécution en cours sur votre téléphone."
    run_output.awaiting_confirmation_step_id = None
    run_output.is_terminal = False
    run_output.visual_feedback = {"type": "execution_requested", "step": updated_step.model_dump()}
    db.add(AuditLog(
        user_id=current_user.id if current_user else None,
        actor_type="user",
        actor_id=current_user.id if current_user else None,
        event_type="STEP_APPROVED",
        resource_type="action",
        resource_id=step.step_id,
        metadata_json={"tool_id": step.tool_id, "parameters": step.parameters},
    ))
    await db.commit()

    return run_output

@router.post("/runs/{run_id}/steps/{step_id}/result", response_model=AgentRunOutput)
async def report_step_result(
    run_id: str,
    step_id: str,
    req: StepResultRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Accept a verified observation from the device; never infer success."""
    run_data = active_runs_store.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Session d'exécution introuvable ou expirée.")
    if run_data["user_id"] is not None and run_data["user_id"] != (current_user.id if current_user else None):
        raise HTTPException(status_code=403, detail="Cette exécution appartient à un autre utilisateur.")

    output: AgentRunOutput = run_data["output"]
    step = next((item for item in output.steps if item.step_id == step_id), None)
    if not step:
        raise HTTPException(status_code=404, detail="Étape introuvable.")
    if step.requires_approval:
        raise HTTPException(status_code=409, detail="L'étape doit être confirmée avant son exécution.")
    if step.status in {"verified", "failed", "unknown"}:
        raise HTTPException(status_code=409, detail="Le résultat de cette étape a déjà été enregistré.")

    step.status, step.result, step.error = req.status, req.result, req.error
    if req.status == "verified":
        if req.result.get("verified") is not True:
            raise HTTPException(status_code=422, detail="Une réussite doit contenir une observation vérifiée.")
        if all(item.status == "verified" for item in output.steps):
            output.state = AgentState.SUCCESS
            output.spoken_response = AgentRuntime._generate_success_speech(output.steps)
            output.is_terminal = True
            output.visual_feedback = {"type": "success", "steps": [item.model_dump() for item in output.steps]}
        else:
            next_approval = next(
                (item for item in output.steps if item.status == "waiting_approval"),
                None,
            )
            if next_approval:
                output.state = AgentState.WAITING_FOR_CONFIRMATION
                output.awaiting_confirmation_step_id = next_approval.step_id
                output.spoken_response = f"Voulez-vous exécuter {next_approval.tool_name} ?"
                output.visual_feedback = {
                    "type": "confirmation_sheet",
                    "step_id": next_approval.step_id,
                    "tool": next_approval.tool_name,
                    "parameters": next_approval.parameters,
                    "risk_level": next_approval.risk_level,
                    "requires_biometric": next_approval.requires_biometric,
                }
            else:
                output.state = AgentState.READY_TO_EXECUTE
                output.spoken_response = "Action suivante prête sur votre téléphone."
    elif req.status == "unknown":
        output.state, output.is_terminal = AgentState.UNKNOWN, False
        output.spoken_response = "L'action a été demandée, mais son résultat n'est pas encore confirmé."
        output.visual_feedback = {"type": "unknown", "step": step.model_dump()}
    else:
        output.state, output.is_terminal = AgentState.FAILED, True
        output.spoken_response = f"Je n'ai pas pu effectuer l'opération : {req.error or 'erreur inconnue'}."
        output.visual_feedback = {"type": "step_failure", "step": step.model_dump()}

    db.add(AuditLog(
        user_id=current_user.id if current_user else None,
        actor_type="device",
        actor_id=None,
        event_type="STEP_RESULT_REPORTED",
        resource_type="action",
        resource_id=step_id,
        metadata_json={"tool_id": step.tool_id, "status": req.status, "result": req.result, "error": req.error},
    ))
    # Elementary anomaly signal: three consecutive failed tool reports from a
    # user are recorded for the admin audit trail. It does not block recovery.
    if req.status == "failed" and current_user:
        recent = await db.execute(select(AuditLog).where(
            AuditLog.user_id == current_user.id,
            AuditLog.event_type == "STEP_RESULT_REPORTED",
        ).order_by(desc(AuditLog.created_at)).limit(2))
        previous = recent.scalars().all()
        if len(previous) == 2 and all(log.metadata_json.get("status") == "failed" for log in previous):
            db.add(AuditLog(
                user_id=current_user.id, actor_type="system", event_type="ANOMALY_SUSPECTED",
                resource_type="agent_run", resource_id=run_id,
                metadata_json={"reason": "three_consecutive_failed_device_actions"},
            ))
    await db.commit()
    return output

@router.post("/runs/{run_id}/cancel", response_model=AgentRunOutput)
async def cancel_run(
    run_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    run_data = active_runs_store.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Exécution introuvable.")

    run_output: AgentRunOutput = run_data["output"]
    run_output.state = AgentState.FAILED
    run_output.spoken_response = "Opération annulée à votre demande."
    run_output.awaiting_confirmation_step_id = None
    run_output.is_terminal = True
    run_output.visual_feedback = {"type": "cancelled"}

    user_id = current_user.id if current_user else None
    audit = AuditLog(
        user_id=user_id,
        actor_type="user",
        actor_id=user_id,
        event_type="ACTION_CANCELLED",
        resource_type="agent_run",
        resource_id=run_id
    )
    db.add(audit)
    await db.commit()

    return run_output

@router.get("/runs/{run_id}", response_model=AgentRunOutput)
async def get_run_status(run_id: str):
    run_data = active_runs_store.get(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Exécution non trouvée.")
    return run_data["output"]
