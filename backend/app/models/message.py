from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class MessageType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"


class ConversationStatus(str, Enum):
    BOT_ACTIVE = "BOT_ACTIVE"
    HUMAN_HANDOFF = "HUMAN_HANDOFF"
    HUMAN_ACTIVE = "HUMAN_ACTIVE"
    CLOSED = "CLOSED"


class NormalizedMessage(BaseModel):
    """Generic message format across all channels"""
    channel: str
    user_id: str
    user_name: Optional[str] = None
    message_id: str
    text: str
    message_type: MessageType = MessageType.TEXT
    timestamp: datetime = None
    metadata: dict = {}

    class Config:
        use_enum_values = True


class ConversationData(BaseModel):
    """Represents a conversation state"""
    channel: str
    user_id: str
    user_name: Optional[str] = None
    status: ConversationStatus = ConversationStatus.BOT_ACTIVE
    last_message: Optional[str] = None
    last_message_timestamp: Optional[datetime] = None
    assigned_to: Optional[str] = None  # Agent ID
    created_at: datetime = None
    updated_at: datetime = None
    message_count: int = 0

    class Config:
        use_enum_values = True


class AgentReply(BaseModel):
    """Agent message payload"""
    text: str
    message_type: MessageType = MessageType.TEXT


class ConversationAssignment(BaseModel):
    """Assign agent to conversation"""
    agent_id: str
