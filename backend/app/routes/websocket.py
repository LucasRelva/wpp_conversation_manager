from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Global instance
websocket_manager = None


def set_websocket_manager(wsm):
    """Inject WebSocket manager"""
    global websocket_manager
    websocket_manager = wsm


@router.websocket("/ws/conversations")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time conversation updates.
    
    Broadcasts:
    - new_message
    - new_handoff
    - conversation_assigned
    - message_sent
    - conversation_closed
    """
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle agent registration
            if message.get("type") == "register_agent":
                agent_id = message.get("agent_id")
                if agent_id:
                    await websocket_manager.register_agent(agent_id, websocket)

            # Handle keep-alive
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket_manager.disconnect(websocket)
