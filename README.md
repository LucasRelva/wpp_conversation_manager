# Channel-Agnostic Human Handoff Dashboard

A generic, webhook-based human handoff system that integrates with ANY messaging platform (WhatsApp, Telegram, Webchat, etc.) without coupling to any specific provider.

## 🎯 Overview

This system provides a unified dashboard for human agents to manage conversations across multiple messaging channels. It features:

- **Channel-Agnostic Architecture**: Works with any webhook-based messaging system
- **Real-Time Updates**: WebSocket support for live conversation updates
- **Conversation Management**: Track, assign, and manage conversations
- **Pluggable Adapters**: Easily add new channels without modifying core logic
- **State Management**: Redis-backed conversation state with automatic persistence
- **Multi-Channel Dashboard**: Single interface for all messaging platforms

## 🏗️ Architecture

### Core Components

1. **Webhook Ingestion Layer** - Accepts messages from any external system
2. **Message Normalizer** - Converts provider-specific formats to standard internal format
3. **Channel Adapter System** - Pluggable interface for different providers
4. **Conversation Manager** - Handles conversation lifecycle and state
5. **State Manager** - Redis-backed persistent storage
6. **REST API** - Full conversation management endpoints
7. **WebSocket Server** - Real-time updates to connected agents
8. **React Dashboard** - Modern web UI for agents

## 🚀 Quick Start with Docker

### Prerequisites
- Docker & Docker Compose
- No other dependencies needed!

### Setup

1. **Clone/Navigate to repository**
   ```bash
   cd wpp_conversation_manager
   ```

2. **Configure environment (optional)**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env if needed (only required for production integrations)
   ```

3. **Start the system**
   ```bash
   docker-compose up --build
   ```

   Services will be available at:
   - **Frontend**: http://localhost:3000
   - **API**: http://localhost:8000
   - **Redis**: localhost:6379
   - **API Docs**: http://localhost:8000/docs (Swagger UI)

4. **Stop the system**
   ```bash
   docker-compose down
   ```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
docker-compose logs -f redis
```

## 🧪 Testing

### 1. Send a Test Message

Use curl to send a message to the webhook:

```bash
# Mock channel (easiest for testing)
curl -X POST http://localhost:8000/api/webhook/mock \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "user_name": "John Doe",
    "message_id": "msg_1",
    "text": "Hello agent!"
  }'

# WhatsApp format
curl -X POST http://localhost:8000/api/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -d '{
    "entry": [{
      "changes": [{
        "value": {
          "messages": [{
            "from": "5511999999999",
            "id": "msg_1",
            "timestamp": "1234567890",
            "text": {"body": "Hello!"}
          }],
          "contacts": [{
            "profile": {"name": "John Doe"},
            "wa_id": "5511999999999"
          }]
        }
      }]
    }]
  }'

# Telegram format
curl -X POST http://localhost:8000/api/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{
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
      "text": "Hello!"
    }
  }'
```

### 2. View in Dashboard

1. Open http://localhost:3000
2. The conversation will appear in the list
3. Click to select and start chatting

### 3. Test Agent Workflow

```bash
# Get all conversations
curl http://localhost:8000/api/conversations

# Assume a conversation
curl -X POST http://localhost:8000/api/conversations/mock/user_123/assume \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_1"}'

# Send agent message
curl -X POST http://localhost:8000/api/conversations/mock/user_123/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Hi! How can I help?"}' \
  -G -d "agent_id=agent_1"

# Close conversation
curl -X POST http://localhost:8000/api/conversations/mock/user_123/close \
  -H "Content-Type: application/json" \
  -d '{"message": "Thank you for contacting us!"}'
```

## 🔌 API Reference

### REST Endpoints

#### Conversations
- `GET /api/conversations` - Get all conversations
- `GET /api/conversations/{channel}/{user_id}` - Get specific conversation with history
- `POST /api/conversations/{channel}/{user_id}/assume` - Assign agent to conversation
- `POST /api/conversations/{channel}/{user_id}/message` - Send agent message
- `POST /api/conversations/{channel}/{user_id}/close` - Close conversation
- `GET /api/handoff-queue` - Get conversations waiting for human handoff
- `GET /api/channels` - List available channels

### WebSocket
- `WS /ws/conversations` - Real-time conversation updates

#### Messages
```json
{
  "type": "new_message",
  "channel": "whatsapp",
  "user_id": "5511999999999",
  "text": "Hello",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Webhooks

#### Incoming Webhook Format

`POST /api/webhook/{channel}`

The system normalizes ANY incoming format through channel-specific adapters.

**Normalized Message** (internal format):
```json
{
  "channel": "whatsapp",
  "user_id": "external_user_id",
  "user_name": "John Doe",
  "message_id": "external_message_id",
  "text": "message content",
  "message_type": "text",
  "timestamp": "2024-01-01T12:00:00Z",
  "metadata": {}
}
```

## 🔌 Adding New Channels

### Step 1: Create Adapter

Create `backend/app/adapters/my_channel.py`:

```python
from app.adapters.base import BaseChannelAdapter
from app.models.message import NormalizedMessage, MessageType
from datetime import datetime

class MyChannelAdapter(BaseChannelAdapter):
    def __init__(self):
        super().__init__("my_channel")

    def parse_incoming(self, payload) -> NormalizedMessage:
        """Parse incoming message from your provider"""
        return NormalizedMessage(
            channel=self.channel_name,
            user_id=payload.get("user_id"),
            user_name=payload.get("user_name"),
            message_id=payload.get("message_id"),
            text=payload.get("text"),
            message_type=MessageType.TEXT,
            timestamp=datetime.now(),
            metadata=payload
        )

    async def send_message(self, user_id: str, text: str) -> bool:
        """Send message via your provider"""
        # Implement sending logic here
        # e.g., call your provider's API
        return True
```

### Step 2: Register Adapter

In `backend/app/adapters/registry.py`, add to `_initialize_default_adapters()`:

```python
from app.adapters.my_channel import MyChannelAdapter
...
self.register_class("my_channel", MyChannelAdapter)
```

### Step 3: Done!

Now you can:
- Send webhooks to `POST /api/webhook/my_channel`
- Messages will be handled automatically
- No other code changes needed!

## 📦 Conversation State

Stored in Redis with these keys:

```
conversation:{channel}:{user_id}      # Conversation metadata
messages:{channel}:{user_id}           # List of message IDs
message:{channel}:{user_id}:{msg_id}   # Individual message
```

### Conversation Statuses
- `BOT_ACTIVE` - Bot is handling the conversation
- `HUMAN_HANDOFF` - Waiting for human agent
- `HUMAN_ACTIVE` - Agent is active
- `CLOSED` - Conversation is closed

## 🛠️ Development

### Local Development (Without Docker)

1. **Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Make sure Redis is running locally
   # Then:
   python run.py
   ```

2. **Frontend**
   ```bash
   cd frontend
   npm install
   npm start
   ```

### Running Tests

```bash
# Backend (add pytest tests as needed)
cd backend
pytest

# Frontend
cd frontend
npm test
```

## 🚨 Key Features

### ✅ Multi-Channel Support
- WhatsApp (adapter included)
- Telegram (adapter included)
- Webchat (adapter included)
- Mock/Test (for development)
- Easily add more!

### ✅ Real-Time Updates
- WebSocket connection for live updates
- Agent presence detection
- Conversation status changes

### ✅ Conversation Management
- View all conversations across channels
- Filter by status (waiting, active)
- Search conversations
- View full conversation history
- Assign agents
- Close conversations

### ✅ Dashboard Features
- Channel badges
- Unread message counters
- Status indicators
- Responsive design
- Message timestamps
- Agent assignment UI

## 🔐 Security Considerations

For production deployment:

1. **Authentication**: Implement agent authentication in the frontend
2. **HTTPS**: Use HTTPS for API and WSS for WebSocket
3. **API Keys**: Set `AGENT_API_KEY` and send it via `Authorization: Bearer <key>` or `X-Agent-API-Key`
4. **Webhook Signatures**: Set `WEBHOOK_SECRET` and validate `X-Webhook-Signature` (`sha256=<hmac>`)
5. **Rate Limiting**: Configure `AGENT_RATE_LIMIT_PER_MINUTE` and `WEBHOOK_RATE_LIMIT_PER_MINUTE`
6. **CORS**: Configure `CORS_ORIGINS` (comma-separated allowlist)
7. **Env Secrets**: Use proper secret management for API tokens
8. **Redis**: Secure Redis with password authentication

## 📊 Monitoring

Monitor these metrics:
- WebSocket connection count
- Message throughput per channel
- Conversation queue length
- Agent workload distribution
- Message response times

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Find and kill process using port
lsof -i :3000
kill -9 <PID>
```

### Redis Connection Failed
```bash
# Check Redis is running
docker-compose logs redis

# Verify connection
redis-cli ping
```

### Frontend Can't Connect to API
- Check `REACT_APP_API_URL` environment variable
- Ensure backend is running on http://localhost:8000
- Check browser console for CORS errors

### Messages Not Appearing
- Check webhook is being called (look at logs)
- Verify message format matches adapter expectations
- Check Redis is storing data: `redis-cli keys "conversation:*"`

## 📝 Environment Variables

### Backend (.env)
```
REDIS_URL=redis://localhost:6379
API_HOST=0.0.0.0
API_PORT=8000
WHATSAPP_API_TOKEN=...        # Optional, for production
TELEGRAM_API_TOKEN=...         # Optional, for production
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000
```

## 🤝 Contributing

To add features or fix bugs:

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a PR

## 📄 License

MIT

## 🙋 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API docs at http://localhost:8000/docs
3. Check logs: `docker-compose logs -f`

---

**Built with**: FastAPI, Redis, React, Docker
