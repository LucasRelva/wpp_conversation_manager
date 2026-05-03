from typing import Any, Dict, Optional
from app.adapters.base import BaseChannelAdapter
from app.models.message import NormalizedMessage, MessageType
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WhatsAppAdapter(BaseChannelAdapter):
    """
    WhatsApp adapter implementation.
    
    Handles parsing of WhatsApp webhook payloads and sending messages
    via WhatsApp Business API.
    """

    def __init__(self, api_token: Optional[str] = None):
        super().__init__("whatsapp")
        self.api_token = api_token
        self.api_url = "https://graph.instagram.com/v18.0"

    def parse_incoming(self, payload: Dict[str, Any]) -> NormalizedMessage:
        """
        Parse WhatsApp webhook payload into normalized format.
        
        Expected WhatsApp webhook format:
        {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "value": {
                        "messages": [{
                            "from": "551199999999",
                            "id": "msg_id",
                            "timestamp": "1234567890",
                            "text": {"body": "message text"}
                        }],
                        "contacts": [{
                            "profile": {"name": "User Name"},
                            "wa_id": "551199999999"
                        }]
                    }
                }]
            }]
        }
        """
        try:
            # Extract from nested WhatsApp webhook structure
            messages = payload.get("entry", [{}])[0].get("changes", [{}])[0] \
                .get("value", {}).get("messages", [])
            contacts = payload.get("entry", [{}])[0].get("changes", [{}])[0] \
                .get("value", {}).get("contacts", [])

            if not messages:
                raise ValueError("No messages in payload")

            message = messages[0]
            contact = contacts[0] if contacts else {}

            user_id = self.extract_user_id(payload)
            user_name = contact.get("profile", {}).get("name")
            message_id = self.extract_message_id(payload)
            text = self.extract_message_text(payload)

            return NormalizedMessage(
                channel=self.channel_name,
                user_id=user_id,
                user_name=user_name,
                message_id=message_id,
                text=text,
                message_type=MessageType.TEXT,
                timestamp=datetime.fromtimestamp(int(message.get("timestamp", 0))),
                metadata={"raw_payload": payload}
            )
        except Exception as e:
            logger.error(f"Error parsing WhatsApp payload: {e}")
            raise

    async def send_message(self, user_id: str, text: str) -> bool:
        """
        Send message via WhatsApp API.
        
        In production, this would call the actual WhatsApp Business API.
        For demo, we'll simulate it.
        """
        if not self.api_token:
            logger.warning(f"WhatsApp token not configured. Would send to {user_id}: {text}")
            return True

        try:
            # In production:
            # import httpx
            # async with httpx.AsyncClient() as client:
            #     response = await client.post(
            #         f"{self.api_url}/me/messages",
            #         json={
            #             "messaging_product": "whatsapp",
            #             "recipient_type": "individual",
            #             "to": user_id,
            #             "type": "text",
            #             "text": {"preview_url": False, "body": text}
            #         },
            #         headers={"Authorization": f"Bearer {self.api_token}"}
            #     )
            #     return response.status_code == 200
            
            logger.info(f"WhatsApp message sent to {user_id}: {text}")
            return True
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    def extract_user_id(self, payload: Dict[str, Any]) -> str:
        """Extract WhatsApp user ID (phone number without +)"""
        try:
            return payload["entry"][0]["changes"][0]["value"]["messages"][0]["from"]
        except (KeyError, IndexError):
            raise ValueError("Could not extract user_id from WhatsApp payload")

    def extract_user_name(self, payload: Dict[str, Any]) -> Optional[str]:
        """Extract WhatsApp user name"""
        try:
            return payload["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
        except (KeyError, IndexError):
            return None

    def extract_message_id(self, payload: Dict[str, Any]) -> str:
        """Extract WhatsApp message ID"""
        try:
            return payload["entry"][0]["changes"][0]["value"]["messages"][0]["id"]
        except (KeyError, IndexError):
            raise ValueError("Could not extract message_id from WhatsApp payload")

    def extract_message_text(self, payload: Dict[str, Any]) -> str:
        """Extract WhatsApp message text"""
        try:
            return payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]
        except (KeyError, IndexError):
            raise ValueError("Could not extract message text from WhatsApp payload")
