from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.services.state_manager import RedisStateManager
from app.services.conversation_manager import ConversationManager
from app.services.websocket_manager import WebSocketManager
from app.routes import api, websocket

logger = logging.getLogger(__name__)

# Global instances
state_manager = None
conversation_manager = None
websocket_manager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.
    
    Handles startup and shutdown of services.
    """
    # Startup
    logger.info("Starting up application...")

    global state_manager, conversation_manager, websocket_manager

    # Initialize Redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    state_manager = RedisStateManager(redis_url)
    await state_manager.connect()

    # Initialize services
    conversation_manager = ConversationManager(state_manager)
    websocket_manager = WebSocketManager()

    # Inject into routes
    api.set_services(conversation_manager, state_manager, websocket_manager)
    websocket.set_websocket_manager(websocket_manager)

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await state_manager.disconnect()
    logger.info("Application shut down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="Channel-Agnostic Handoff Dashboard",
        description="Generic webhook-based human handoff system for any messaging platform",
        version="1.0.0",
        lifespan=lifespan
    )

    cors_origins = os.getenv("CORS_ORIGINS", "*")
    allow_origins = [origin.strip() for origin in cors_origins.split(",") if origin.strip()]

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routes
    app.include_router(api.router, prefix="/api", tags=["conversations"])
    app.include_router(websocket.router, tags=["websocket"])

    # Health check
    @app.get("/health")
    async def health_check():
        redis_ok = False
        if state_manager and state_manager.redis:
            try:
                redis_ok = bool(await state_manager.redis.ping())
            except Exception:
                redis_ok = False

        status = "healthy" if redis_ok else "degraded"
        return {
            "status": status,
            "service": "channel-agnostic-handoff-dashboard",
            "redis": "up" if redis_ok else "down"
        }

    @app.get("/ready")
    async def readiness_check():
        if not state_manager or not state_manager.redis:
            return {"ready": False, "reason": "redis_not_initialized"}

        try:
            await state_manager.redis.ping()
            return {"ready": True}
        except Exception:
            return {"ready": False, "reason": "redis_unavailable"}

    return app


app = create_app()
