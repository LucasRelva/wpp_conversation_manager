# Architecture & Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     External Messaging Systems                   │
│  WhatsApp │ Telegram │ Webchat │ SMS │ Slack │ Custom...        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP Webhooks
                       ▼
        ┌──────────────────────────────────┐
        │   Webhook Ingestion Layer        │
        │  POST /webhook/{channel}         │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │  Channel Adapter System          │
        │  (Pluggable Parsers)             │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ Message Normalizer               │
        │ → NormalizedMessage              │
        └──────────────┬───────────────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ Conversation Manager             │
        │ (Business Logic & Handoff)       │
        └──────────────┬───────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
    ┌────────┐  ┌─────────────┐  ┌──────────┐
    │ Redis  │  │  REST API   │  │ WebSocket│
    │        │  │ (HTTP)      │  │          │
    └────────┘  └──────┬──────┘  └─────┬────┘
                       │               │
                       └───────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │ React Dashboard     │
                    │ (Agent Interface)   │
                    └─────────────────────┘
```

## Component Details

### 1. Channel Adapters

Each adapter implements `BaseChannelAdapter` with:

```python
class BaseChannelAdapter:
    async def parse_incoming(payload) -> NormalizedMessage
    async def send_message(user_id, text) -> bool
```

**Built-in Adapters**:
- `WhatsAppAdapter` - WhatsApp Business API format
- `TelegramAdapter` - Telegram Bot API format
- `WebchatAdapter` - Web chat format
- `MockAdapter` - For testing

### 2. Message Normalization

All messages are converted to this standard format:

```json
{
  "channel": "whatsapp",
  "user_id": "5511999999999",
  "user_name": "John Doe",
  "message_id": "wamid.123",
  "text": "Hello!",
  "message_type": "text",
  "timestamp": "2024-01-01T12:00:00Z",
  "metadata": {}
}
```

### 3. Conversation States

```
BOT_ACTIVE ──→ HUMAN_HANDOFF ──→ HUMAN_ACTIVE ──→ CLOSED
  │ System      │ Queued for     │ Agent active    │ Ended
  │ responding  │ agent          │ 1-on-1 chat     │
```

### 4. Redis Keys Structure

```
conversation:whatsapp:5511999999999
│ {
│   "channel": "whatsapp",
│   "user_id": "5511999999999",
│   "user_name": "John Doe",
│   "status": "HUMAN_ACTIVE",
│   "assigned_to": "agent_1",
│   "last_message": "Thank you!",
│   "last_message_timestamp": "2024-01-01T12:00:00Z",
│   "message_count": 5,
│   ...
│ }

messages:whatsapp:5511999999999
│ [msg_id_5, msg_id_4, msg_id_3, msg_id_2, msg_id_1] (LIFO)

message:whatsapp:5511999999999:msg_id_1
│ {
│   "channel": "whatsapp",
│   "user_id": "5511999999999",
│   "message_id": "msg_id_1",
│   "text": "Hello!",
│   "timestamp": "2024-01-01T12:00:00Z",
│   ...
│ }
```

## API Design

### REST Endpoints

**Conversations Management**
- `GET /api/conversations` - List all
- `GET /api/conversations/{channel}/{user_id}` - Get with history
- `POST /api/conversations/{channel}/{user_id}/assume` - Assign agent
- `POST /api/conversations/{channel}/{user_id}/message` - Send message
- `POST /api/conversations/{channel}/{user_id}/close` - Close

**Utilities**
- `GET /api/handoff-queue` - Get waiting conversations
- `GET /api/channels` - List available channels
- `GET /health` - Health check

### WebSocket Events

**Incoming (from client)**:
```json
{
  "type": "register_agent",
  "agent_id": "agent_1"
}
```

**Outgoing (to clients)**:
```json
{
  "type": "new_message",
  "channel": "whatsapp",
  "user_id": "5511999999999",
  "text": "Hello!",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Data Flow Example

### 1. Incoming Message
```
External System (WhatsApp)
    ↓ (webhook)
POST /api/webhook/whatsapp
    ↓
WhatsAppAdapter.parse_incoming()
    ↓
NormalizedMessage
    ↓
ConversationManager.handle_incoming_message()
    ↓
StateManager saves to Redis
    ↓
Broadcast via WebSocket to connected agents
    ↓
React Dashboard updates in real-time
```

### 2. Agent Takes Conversation
```
Agent clicks "Assume" in Dashboard
    ↓
Frontend: POST /api/conversations/whatsapp/{user_id}/assume
    ↓
ConversationManager.assign_agent()
    ↓
Update status: HUMAN_HANDOFF → HUMAN_ACTIVE
Update assignment: null → agent_1
    ↓
Send message to user via adapter
    ↓
Broadcast via WebSocket
    ↓
Dashboard updates conversation status
```

### 3. Agent Sends Reply
```
Agent types message and clicks Send
    ↓
Frontend: POST /api/conversations/whatsapp/{user_id}/message
    ↓
ConversationManager.send_agent_message()
    ↓
WhatsAppAdapter.send_message()
    ↓
Message sent via WhatsApp API
    ↓
Save to Redis
    ↓
Broadcast via WebSocket
    ↓
Message appears in Dashboard
```

## Scalability Considerations

### Current Setup
- Single Redis instance
- Single API instance
- Perfect for small to medium workloads

### For Higher Scale

1. **Horizontal API Scaling**
   - Load balance multiple API instances
   - Use Redis Pub/Sub for cross-instance messaging
   - Share state via Redis

2. **WebSocket Scaling**
   - Use Redis Pub/Sub for multi-instance broadcasting
   - Sticky sessions or distributed cache

3. **Storage Scaling**
   - Move old messages to persistent database
   - Archive closed conversations
   - Keep only recent conversations in Redis

4. **Monitoring**
   - Add Prometheus metrics
   - Track queue depth
   - Monitor agent utilization

## Security Architecture

### Current (Development)
- Open CORS
- No authentication
- No HTTPS
- No rate limiting

### For Production

1. **Authentication Layer**
   ```python
   @app.middleware("http")
   async def verify_auth(request, call_next):
       token = request.headers.get("Authorization")
       if not verify_token(token):
           return 403
       return await call_next(request)
   ```

2. **Webhook Signature Verification**
   ```python
   # For WhatsApp webhooks
   if not verify_webhook_signature(payload, signature):
       return 403
   ```

3. **Rate Limiting**
   ```python
   # Per IP, per agent, per channel
   limiter = Limiter(key_func=get_remote_address)
   @limiter.limit("100/minute")
   ```

4. **TLS/SSL**
   - HTTPS for API
   - WSS for WebSocket
   - Nginx reverse proxy

5. **Redis Security**
   - Password authentication
   - TCP binding to internal network only
   - Redis Sentinel for HA

## Error Handling

### Webhook Errors
- `400 Bad Request` - Invalid payload format
- `404 Not Found` - Channel not registered
- `500 Internal Server Error` - Processing failure

### API Errors
- `404 Not Found` - Conversation not found
- `422 Unprocessable Entity` - Invalid request body
- `500 Internal Server Error` - Server error

### Retry Logic
- Messages: 3 retries with exponential backoff
- Webhooks: Provider retries (configure on provider side)
- WebSocket: Auto-reconnect with backoff

## Testing Strategy

### Unit Tests
- Adapter parsing (various formats)
- Conversation state transitions
- Message normalization

### Integration Tests
- Full webhook → storage → broadcast flow
- Multi-adapter scenarios
- Concurrent message handling

### End-to-End Tests
- Dashboard interaction
- Real-time WebSocket updates
- Full conversation lifecycle

## Monitoring & Metrics

### Key Metrics
- Messages per second (by channel)
- Conversation queue length
- Average response time
- Agent utilization
- WebSocket connection count
- Redis memory usage

### Alerts
- Queue depth > threshold
- Response time > threshold
- Redis connection lost
- Webhook failure rate > threshold
