import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from app.database.session import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    phone = Column(String(32), unique=True, index=True, nullable=False)
    display_name = Column(String(128), nullable=True)
    hashed_password = Column(String(256), nullable=True)
    locale = Column(String(16), default="fr")
    timezone = Column(String(64), default="Africa/Abidjan")
    status = Column(String(32), default="active")  # active, suspended, pending
    role = Column(String(32), default="user")  # user, admin, super_admin, support
    vulnerable_mode = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")

class Device(Base):
    __tablename__ = "devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_identifier = Column(String(128), unique=True, nullable=False, index=True)
    platform = Column(String(32), default="android")
    android_version = Column(String(32), nullable=True)
    app_version = Column(String(32), default="1.0.0")
    last_seen_at = Column(DateTime(timezone=True), default=utc_now)
    trust_status = Column(String(32), default="trusted")  # trusted, untrusted, revoked
    created_at = Column(DateTime(timezone=True), default=utc_now)

    user = relationship("User", back_populates="devices")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(36), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), default=utc_now)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(32), default="active")  # active, expired, terminated
    authentication_level = Column(String(32), default="standard")  # standard, strong_biometric

    user = relationship("User", back_populates="sessions")

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(36), nullable=True)
    title = Column(String(256), default="Nouvelle conversation")
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    intents = relationship("Intent", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(32), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    content_type = Column(String(32), default="text")  # text, audio_transcript, system_notice
    language = Column(String(16), default="fr")
    created_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="messages")

class Intent(Base):
    __tablename__ = "intents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(36), nullable=True)
    intent_name = Column(String(64), nullable=False)
    parameters = Column(JSON, default=dict)
    confidence = Column(Float, default=1.0)
    status = Column(String(32), default="resolved")  # resolved, ambiguous, rejected
    created_at = Column(DateTime(timezone=True), default=utc_now)

    conversation = relationship("Conversation", back_populates="intents")
    agent_runs = relationship("AgentRun", back_populates="intent", cascade="all, delete-orphan")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    intent_id = Column(String(36), ForeignKey("intents.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(32), default="RECEIVED")  
    # RECEIVED, UNDERSTANDING, CONTEXT_ENRICHMENT, PLANNING, POLICY_CHECK, RISK_ASSESSMENT,
    # WAITING_FOR_CLARIFICATION, WAITING_FOR_CONFIRMATION, READY_TO_EXECUTE, EXECUTING,
    # OBSERVING, VERIFYING, SUCCESS, FAILED, UNKNOWN, RECOVERY
    started_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_code = Column(String(64), nullable=True)
    execution_plan = Column(JSON, default=list)

    intent = relationship("Intent", back_populates="agent_runs")
    actions = relationship("Action", back_populates="agent_run", cascade="all, delete-orphan")

class Action(Base):
    __tablename__ = "actions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(String(64), nullable=False)
    risk_level = Column(Integer, default=1)  # 0, 1, 2, 3, 4
    status = Column(String(32), default="pending")  # pending, waiting_approval, executing, verified, failed, cancelled
    input_payload = Column(JSON, default=dict)
    output_payload = Column(JSON, nullable=True)
    idempotency_key = Column(String(128), index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    agent_run = relationship("AgentRun", back_populates="actions")
    approvals = relationship("Approval", back_populates="action", cascade="all, delete-orphan")

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_id = Column(String(36), ForeignKey("actions.id", ondelete="CASCADE"), nullable=False, index=True)
    required = Column(Boolean, default=True)
    status = Column(String(32), default="pending")  # pending, approved, rejected, expired
    method = Column(String(32), default="voice_or_touch")  # voice, touch, biometric, pin
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(String(36), nullable=True)

    action = relationship("Action", back_populates="approvals")

class ToolModel(Base):
    __tablename__ = "tools"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    version = Column(String(32), default="1.0.0")
    provider = Column(String(64), default="device")  # device, mcp, native, partner
    risk_level = Column(Integer, default=1)
    enabled = Column(Boolean, default=True)
    configuration = Column(JSON, default=dict)

class PolicyModel(Base):
    __tablename__ = "policies"

    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    version = Column(String(32), default="1.0.0")
    scope = Column(String(64), default="global")
    rules = Column(JSON, default=dict)
    enabled = Column(Boolean, default=True)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_id = Column(String(36), ForeignKey("actions.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(64), nullable=False)  # wave, orange_money, mtn, sandbox
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="XOF")
    recipient = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=False)
    status = Column(String(32), default="pending")  # pending, confirmed, submitted, verified, failed, unknown
    provider_reference = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

class TransactionEvent(Base):
    __tablename__ = "transaction_events"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False)
    payload = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now)

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True, index=True)
    device_id = Column(String(36), nullable=True, index=True)
    actor_type = Column(String(32), default="user")  # user, agent, admin, system
    actor_id = Column(String(36), nullable=True)
    event_type = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(64), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utc_now, index=True)
