from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from app.models.message import NormalizedMessage
import json
from datetime import datetime


class BaseChannelAdapter(ABC):
    """
    Base class for all channel adapters.
    
    Each channel (WhatsApp, Telegram, Webchat, etc.) must implement
    this interface to enable the system to work generically with any provider.
    """

    def __init__(self, channel_name: str):
        self.channel_name = channel_name

    @abstractmethod
    def parse_incoming(self, payload: Dict[str, Any]) -> NormalizedMessage:
        """
        Convert incoming payload from external provider into normalized format.
        
        Args:
            payload: Raw webhook payload from external provider
            
        Returns:
            NormalizedMessage: Standardized message format
        """
        pass

    @abstractmethod
    async def send_message(self, user_id: str, text: str) -> bool:
        """
        Send a message to user via this channel.
        
        Args:
            user_id: External user identifier
            text: Message text to send
            
        Returns:
            bool: Success status
        """
        pass

    def extract_user_id(self, payload: Dict[str, Any]) -> str:
        """Extract user identifier from payload. Override if needed."""
        raise NotImplementedError()

    def extract_user_name(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract user name from payload. Override if needed."""
        return None

    def extract_message_id(self, payload: Dict[str, Any]) -> str:
        """Extract unique message identifier. Override if needed."""
        raise NotImplementedError()

    def extract_message_text(self, payload: Dict[str, Any]) -> str:
        """Extract message text from payload. Override if needed."""
        raise NotImplementedError()
