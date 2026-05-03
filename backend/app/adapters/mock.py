from typing import Any, Dict, Optional
from app.adapters.base import BaseChannelAdapter
from app.models.message import NormalizedMessage, MessageType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MockAdapter(BaseChannelAdapter):
    """Mock adapter for testing purposes."""

    def __init__(self):
        super().__init__("mock")

    def parse_incoming(self, payload: Dict[str, Any]) -> NormalizedMessage:
        """Parse mock payload - expects simple structure"""
        return NormalizedMessage(
            channel=self.channel_name,
            user_id=payload.get("user_id", "test_user"),
            user_name=payload.get("user_name", "Test User"),
            message_id=payload.get("message_id", "mock_msg_1"),
            text=payload.get("text", ""),
            message_type=MessageType.TEXT,
            timestamp=datetime.now(),
            metadata=payload
        )

    async def send_message(self, user_id: str, text: str) -> bool:
        """Mock send - just log it"""
        logger.info(f"[MOCK] Message to {user_id}: {text}")
        return True


class TelegramAdapter(BaseChannelAdapter):
    """Telegram adapter implementation."""

    def __init__(self, api_token: Optional[str] = None):
        super().__init__("telegram")
        self.api_token = api_token
        self.api_url = "https://api.telegram.org/bot"

    def parse_incoming(self, payload: Dict[str, Any]) -> NormalizedMessage:
        """
        Parse Telegram webhook payload.
        
        Expected format:
        {
            "update_id": 123456,
            "message": {
                "message_id": 789,
                "from": {
                    "id": 987654321,
                    "first_name": "John",
                    "last_name": "Doe"
                },
                "chat": {"id": 987654321},
                "date": 1234567890,
                "text": "Hello"
            }
        }
        """
        try:
            message = payload.get("message", {})
            from_user = message.get("from", {})
            user_id = str(from_user.get("id"))
            user_name = from_user.get("first_name")

            return NormalizedMessage(
                channel=self.channel_name,
                user_id=user_id,
                user_name=user_name,
                message_id=str(message.get("message_id")),
                text=message.get("text", ""),
                message_type=MessageType.TEXT,
                timestamp=datetime.fromtimestamp(message.get("date", 0)),
                metadata={"raw_payload": payload}
            )
        except Exception as e:
            logger.error(f"Error parsing Telegram payload: {e}")
            raise

    async def send_message(self, user_id: str, text: str) -> bool:
        """Send message via Telegram API"""
        if not self.api_token:
            logger.warning(f"Telegram token not configured. Would send to {user_id}: {text}")
            return True

        try:
            # In production:
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         f"{self.api_url}{self.api_token}/sendMessage",
            #         json={"chat_id": user_id, "text": text}
            #     )
            #     return response.status_code == 200
            
            logger.info(f"[Telegram] Message to {user_id}: {text}")
            return True
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False


class WebchatAdapter(BaseChannelAdapter):
    """Webchat adapter implementation."""

    def __init__(self):
        super().__init__("webchat")

    def parse_incoming(self, payload: Dict[str, Any]) -> NormalizedMessage:
        """
        Parse webchat payload.
        
        Expected format:
        {
            "session_id": "session_123",
            "visitor_name": "John Doe",
            "message": "Hello",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        """
        try:
            return NormalizedMessage(
                channel=self.channel_name,
                user_id=payload.get("session_id", "web_user"),
                user_name=payload.get("visitor_name"),
                message_id=payload.get("message_id", f"web_{payload.get('session_id')}_msg"),
                text=payload.get("message", ""),
                message_type=MessageType.TEXT,
                timestamp=datetime.fromisoformat(
                    payload.get("timestamp", "").replace("Z", "+00:00")
                ) if payload.get("timestamp") else datetime.now(),
                metadata={"raw_payload": payload}
            )
        except Exception as e:
            logger.error(f"Error parsing Webchat payload: {e}")
            raise

    async def send_message(self, user_id: str, text: str) -> bool:
        """Send message via webchat - would push to session"""
        logger.info(f"[Webchat] Message to session {user_id}: {text}")
        return True
