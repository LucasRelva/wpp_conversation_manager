from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

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
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
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
