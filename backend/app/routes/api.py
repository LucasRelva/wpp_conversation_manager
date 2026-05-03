from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List
from app.models.message import (
    NormalizedMessage,
    ConversationData,
    AgentReply,
    ConversationAssignment
)
from app.services.conversation_manager import ConversationManager
from app.services.state_manager import RedisStateManager
from app.adapters.registry import adapter_registry
from app.security import require_agent_api_key, verify_webhook_secret
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instances (will be initialized in main app)
conversation_manager: ConversationManager = None
state_manager: RedisStateManager = None
websocket_manager = None


def set_services(cm: ConversationManager, sm: RedisStateManager, ws_mgr):
    """Inject services (called from main app)"""
    global conversation_manager, state_manager, websocket_manager
    conversation_manager = cm
    state_manager = sm
    websocket_manager = ws_mgr


@router.post("/webhook/{channel}")
async def webhook_handler(
    channel: str,
    payload: dict,
    request: Request
) -> dict:
    """
    Accept webhook messages from any channel.
    
    POST /webhook/whatsapp
    POST /webhook/telegram
    POST /webhook/webchat
    etc.
    """
    try:
        await verify_webhook_secret(request)

        # Get adapter for this channel
        adapter = adapter_registry.get_adapter(channel)

        # Parse incoming message
        message = adapter.parse_incoming(payload)

        # Process message
        conversation = await conversation_manager.handle_incoming_message(message)

        # Notify via WebSocket
        await websocket_manager.broadcast({
            "type": "new_message",
            "channel": channel,
            "user_id": message.user_id,
            "message_id": message.message_id,
            "text": message.text,
            "user_name": message.user_name,
            "timestamp": message.timestamp.isoformat() if message.timestamp else None
        })

        return {
            "success": True,
            "channel": channel,
            "user_id": message.user_id,
            "status": conversation.status
        }

    except ValueError as e:
        logger.error(f"Invalid payload for {channel}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations")
async def get_conversations() -> List[dict]:
    """Get all active conversations across all channels"""
    try:
        conversations = await conversation_manager.get_all_conversations()

        return [
            {
                "channel": c.channel,
                "user_id": c.user_id,
                "name": c.user_name or "Unknown",
                "status": c.status,
                "last_message": c.last_message,
                "last_message_timestamp": c.last_message_timestamp.isoformat()
                if c.last_message_timestamp else None,
                "assigned_to": c.assigned_to,
                "message_count": c.message_count,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in conversations
        ]
    except Exception as e:
        logger.error(f"Error fetching conversations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations/{channel}/{user_id}")
async def get_conversation(channel: str, user_id: str) -> dict:
    """Get specific conversation with full history"""
    try:
        conversation = await state_manager.get_conversation(channel, user_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = await conversation_manager.get_conversation_history(channel, user_id)

        return {
            "conversation": {
                "channel": conversation.channel,
                "user_id": conversation.user_id,
                "name": conversation.user_name,
                "status": conversation.status,
                "assigned_to": conversation.assigned_to,
                "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
                "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
            },
            "messages": [
                {
                    "message_id": m.message_id,
                    "text": m.text,
                    "timestamp": m.timestamp.isoformat() if m.timestamp else None,
                    "user_name": m.user_name,
                    "metadata": m.metadata
                }
                for m in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{channel}/{user_id}/assume")
async def assume_conversation(
    channel: str,
    user_id: str,
    assignment: ConversationAssignment,
    _: None = Depends(require_agent_api_key)
) -> dict:
    """Assume (assign agent to) a conversation"""
    try:
        success = await conversation_manager.assign_agent(
            channel,
            user_id,
            assignment.agent_id
        )

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Broadcast assignment event
        await websocket_manager.broadcast({
            "type": "conversation_assigned",
            "channel": channel,
            "user_id": user_id,
            "agent_id": assignment.agent_id
        })

        return {
            "success": True,
            "channel": channel,
            "user_id": user_id,
            "assigned_to": assignment.agent_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assigning conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{channel}/{user_id}/message")
async def send_agent_message(
    channel: str,
    user_id: str,
    reply: AgentReply,
    agent_id: str,
    _: None = Depends(require_agent_api_key)
) -> dict:
    """Send message from agent to user"""
    try:
        success = await conversation_manager.send_agent_message(
            channel,
            user_id,
            reply.text,
            agent_id
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to send message")

        # Broadcast message event
        await websocket_manager.broadcast({
            "type": "message_sent",
            "channel": channel,
            "user_id": user_id,
            "message_id": f"agent_{agent_id}_{int(time.time() * 1000)}",
            "agent_id": agent_id,
            "text": reply.text,
            "timestamp": None
        })

        return {
            "success": True,
            "channel": channel,
            "user_id": user_id,
            "message": reply.text
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/conversations/{channel}/{user_id}/close")
async def close_conversation(
    channel: str,
    user_id: str,
    closing_message: dict = None,
    _: None = Depends(require_agent_api_key)
) -> dict:
    """Close a conversation"""
    try:
        message_text = closing_message.get("message") if closing_message else None
        success = await conversation_manager.close_conversation(
            channel,
            user_id,
            message_text
        )

        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")

        return {
            "success": True,
            "channel": channel,
            "user_id": user_id,
            "status": "CLOSED"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error closing conversation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/handoff-queue")
async def get_handoff_queue() -> List[dict]:
    """Get conversations waiting for human handoff"""
    try:
        queue = await conversation_manager.get_handoff_queue()
        return [
            {
                "channel": c.channel,
                "user_id": c.user_id,
                "name": c.user_name or "Unknown",
                "last_message": c.last_message,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in queue
        ]
    except Exception as e:
        logger.error(f"Error fetching handoff queue: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/channels")
async def list_channels() -> dict:
    """List available channels"""
    try:
        channels = adapter_registry.list_channels()
        return {"channels": channels}
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
