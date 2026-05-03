import json
import redis.asyncio as redis
from typing import Optional, List, Dict, Any
from app.models.message import ConversationData, ConversationStatus, NormalizedMessage
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RedisStateManager:
    """
    Manages conversation state in Redis.
    
    Keys:
    - conversation:{channel}:{user_id}: Conversation metadata
    - messages:{channel}:{user_id}: List of message IDs
    - message:{channel}:{user_id}:{message_id}: Message content
    - status:{channel}:{user_id}: Current status
    - assignment:{channel}:{user_id}: Assigned agent
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None

    async def connect(self):
        """Initialize Redis connection"""
        self.redis = await redis.from_url(self.redis_url, decode_responses=True)
        logger.info("Connected to Redis")

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def save_message(
        self,
        channel: str,
        user_id: str,
        message: NormalizedMessage
    ) -> bool:
        """Save normalized message"""
        try:
            message_key = f"message:{channel}:{user_id}:{message.message_id}"
            messages_list_key = f"messages:{channel}:{user_id}"

            # Save message data
            message_data = message.model_dump_json()
            await self.redis.set(message_key, message_data, ex=7*24*3600)  # 7 days TTL

            # Add to messages list
            await self.redis.lpush(messages_list_key, message.message_id)

            # Update conversation metadata
            await self._update_conversation_metadata(channel, user_id, message)

            return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False

    async def get_messages(
        self,
        channel: str,
        user_id: str,
        limit: int = 50
    ) -> List[NormalizedMessage]:
        """Get recent messages for a conversation"""
        try:
            messages_list_key = f"messages:{channel}:{user_id}"
            message_ids = await self.redis.lrange(messages_list_key, 0, limit - 1)

            messages = []
            for msg_id in reversed(message_ids):  # Reverse to get chronological order
                message_key = f"message:{channel}:{user_id}:{msg_id}"
                message_data = await self.redis.get(message_key)
                if message_data:
                    messages.append(NormalizedMessage.parse_raw(message_data))

            return messages
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return []

    async def get_conversation(self, channel: str, user_id: str) -> Optional[ConversationData]:
        """Get conversation metadata"""
        try:
            conversation_key = f"conversation:{channel}:{user_id}"
            data = await self.redis.get(conversation_key)
            if data:
                return ConversationData.parse_raw(data)
            return None
        except Exception as e:
            logger.error(f"Error retrieving conversation: {e}")
            return None

    async def _update_conversation_metadata(
        self,
        channel: str,
        user_id: str,
        message: NormalizedMessage
    ):
        """Update conversation metadata after new message"""
        conversation_key = f"conversation:{channel}:{user_id}"

        # Get or create conversation
        existing = await self.get_conversation(channel, user_id)

        if existing:
            conversation = existing
            conversation.message_count += 1
        else:
            conversation = ConversationData(
                channel=channel,
                user_id=user_id,
                user_name=message.user_name,
                status=ConversationStatus.BOT_ACTIVE,
                created_at=datetime.now(),
                message_count=1
            )

        conversation.last_message = message.text
        conversation.last_message_timestamp = message.timestamp
        conversation.updated_at = datetime.now()

        await self.redis.set(
            conversation_key,
            conversation.model_dump_json(),
            ex=30*24*3600  # 30 days TTL
        )

    async def set_status(self, channel: str, user_id: str, status: ConversationStatus) -> bool:
        """Set conversation status"""
        try:
            conversation = await self.get_conversation(channel, user_id)
            if conversation:
                conversation.status = status
                conversation.updated_at = datetime.now()
                conversation_key = f"conversation:{channel}:{user_id}"
                await self.redis.set(
                    conversation_key,
                    conversation.model_dump_json(),
                    ex=30*24*3600
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting status: {e}")
            return False

    async def assign_agent(
        self,
        channel: str,
        user_id: str,
        agent_id: str
    ) -> bool:
        """Assign agent to conversation"""
        try:
            conversation = await self.get_conversation(channel, user_id)
            if conversation:
                conversation.assigned_to = agent_id
                conversation.status = ConversationStatus.HUMAN_ACTIVE
                conversation.updated_at = datetime.now()
                conversation_key = f"conversation:{channel}:{user_id}"
                await self.redis.set(
                    conversation_key,
                    conversation.model_dump_json(),
                    ex=30*24*3600
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error assigning agent: {e}")
            return False

    async def get_all_conversations(self) -> List[ConversationData]:
        """Get all active conversations"""
        try:
            # Find all conversation keys
            pattern = "conversation:*"
            keys = await self.redis.keys(pattern)

            conversations = []
            for key in keys:
                data = await self.redis.get(key)
                if data:
                    conversations.append(ConversationData.parse_raw(data))

            return sorted(
                conversations,
                key=lambda c: c.updated_at or datetime.now(),
                reverse=True
            )
        except Exception as e:
            logger.error(f"Error retrieving all conversations: {e}")
            return []

    async def close_conversation(self, channel: str, user_id: str) -> bool:
        """Close a conversation"""
        try:
            conversation = await self.get_conversation(channel, user_id)
            if conversation:
                conversation.status = ConversationStatus.CLOSED
                conversation.updated_at = datetime.now()
                conversation_key = f"conversation:{channel}:{user_id}"
                await self.redis.set(
                    conversation_key,
                    conversation.model_dump_json(),
                    ex=30*24*3600
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error closing conversation: {e}")
            return False

    async def get_handoff_queue(self) -> List[ConversationData]:
        """Get conversations awaiting human handoff"""
        try:
            all_convs = await self.get_all_conversations()
            return [c for c in all_convs if c.status == ConversationStatus.HUMAN_HANDOFF]
        except Exception as e:
            logger.error(f"Error retrieving handoff queue: {e}")
            return []

    async def get_agent_conversations(self, agent_id: str) -> List[ConversationData]:
        """Get conversations assigned to an agent"""
        try:
            all_convs = await self.get_all_conversations()
            return [c for c in all_convs if c.assigned_to == agent_id]
        except Exception as e:
            logger.error(f"Error retrieving agent conversations: {e}")
            return []
