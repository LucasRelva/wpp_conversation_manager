from typing import Optional, List
from app.models.message import NormalizedMessage, ConversationData, ConversationStatus
from app.services.state_manager import RedisStateManager
from app.adapters.registry import adapter_registry
import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """
    Manages conversation lifecycle and handoff logic.
    
    Handles:
    - Incoming messages
    - Conversation state transitions
    - Agent assignment
    - Outgoing message routing
    """

    def __init__(self, state_manager: RedisStateManager):
        self.state_manager = state_manager

    async def handle_incoming_message(self, message: NormalizedMessage) -> ConversationData:
        """
        Process incoming message.
        
        This is the main entry point for webhook messages.
        """
        logger.info(f"Handling incoming message from {message.channel}:{message.user_id}")

        # Save message
        await self.state_manager.save_message(
            message.channel,
            message.user_id,
            message
        )

        # Get or create conversation
        conversation = await self.state_manager.get_conversation(
            message.channel,
            message.user_id
        )

        if not conversation:
            # Create new conversation
            conversation = ConversationData(
                channel=message.channel,
                user_id=message.user_id,
                user_name=message.user_name,
                status=ConversationStatus.BOT_ACTIVE,
            )

        # Update last message
        conversation.last_message = message.text
        conversation.last_message_timestamp = message.timestamp

        logger.info(f"Conversation state: {conversation.status}")

        return conversation

    async def request_human_handoff(
        self,
        channel: str,
        user_id: str
    ) -> bool:
        """Request human handoff for a conversation"""
        logger.info(f"Requesting handoff for {channel}:{user_id}")

        # Update status
        success = await self.state_manager.set_status(
            channel,
            user_id,
            ConversationStatus.HUMAN_HANDOFF
        )

        if success:
            # Send handoff message to user
            adapter = adapter_registry.get_adapter(channel)
            await adapter.send_message(
                user_id,
                "You are being connected to a human agent. Please wait... 🙂"
            )

        return success

    async def assign_agent(
        self,
        channel: str,
        user_id: str,
        agent_id: str
    ) -> bool:
        """Assign agent to conversation"""
        logger.info(f"Assigning agent {agent_id} to {channel}:{user_id}")

        success = await self.state_manager.assign_agent(channel, user_id, agent_id)

        if success:
            # Send notification to user
            adapter = adapter_registry.get_adapter(channel)
            await adapter.send_message(
                user_id,
                f"An agent has been assigned. They will respond shortly."
            )

        return success

    async def send_agent_message(
        self,
        channel: str,
        user_id: str,
        text: str,
        agent_id: str
    ) -> bool:
        """
        Send message from agent to user.
        
        Routes through appropriate channel adapter.
        """
        logger.info(f"Agent {agent_id} sending message to {channel}:{user_id}")

        # Get adapter
        adapter = adapter_registry.get_adapter(channel)

        # Send via adapter
        success = await adapter.send_message(user_id, text)

        if success:
            # Create agent message and store
            agent_message = NormalizedMessage(
                channel=channel,
                user_id=user_id,
                user_name=f"Agent: {agent_id}",
                message_id=f"agent_{agent_id}_{int(__import__('time').time()*1000)}",
                text=text,
                metadata={"agent_id": agent_id, "is_outgoing": True}
            )
            await self.state_manager.save_message(channel, user_id, agent_message)

        return success

    async def close_conversation(
        self,
        channel: str,
        user_id: str,
        closing_message: Optional[str] = None
    ) -> bool:
        """Close a conversation"""
        logger.info(f"Closing conversation {channel}:{user_id}")

        # Send closing message if provided
        if closing_message:
            adapter = adapter_registry.get_adapter(channel)
            await adapter.send_message(user_id, closing_message)

        # Update status
        return await self.state_manager.set_status(
            channel,
            user_id,
            ConversationStatus.CLOSED
        )

    async def get_all_conversations(self) -> List[ConversationData]:
        """Get all active conversations"""
        return await self.state_manager.get_all_conversations()

    async def get_handoff_queue(self) -> List[ConversationData]:
        """Get conversations awaiting handoff"""
        return await self.state_manager.get_handoff_queue()

    async def get_conversation_history(
        self,
        channel: str,
        user_id: str,
        limit: int = 50
    ) -> List[NormalizedMessage]:
        """Get conversation message history"""
        return await self.state_manager.get_messages(channel, user_id, limit)
