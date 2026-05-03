# Testing Guide

## Overview

This guide explains how to test the Handoff Dashboard system at different levels.

## Unit Tests

### Running Backend Unit Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Writing Tests

Create `tests/test_adapters.py`:

```python
import pytest
from app.adapters.whatsapp import WhatsAppAdapter
from app.models.message import NormalizedMessage

def test_whatsapp_adapter_parse():
    adapter = WhatsAppAdapter()
    
    payload = {
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
                        "profile": {"name": "John"},
                        "wa_id": "5511999999999"
                    }]
                }
            }]
        }]
    }
    
    message = adapter.parse_incoming(payload)
    
    assert message.channel == "whatsapp"
    assert message.user_id == "5511999999999"
    assert message.text == "Hello!"
    assert message.user_name == "John"
```

## Integration Tests

### API Integration Tests

```bash
# Start services
docker-compose up -d

# Run integration tests
python tests/integration/test_api.py
```

Example test:

```python
import httpx
import pytest

BASE_URL = "http://localhost:8000/api"

@pytest.mark.asyncio
async def test_webhook_and_conversation_flow():
    async with httpx.AsyncClient() as client:
        # 1. Send message
        response = await client.post(
            f"{BASE_URL}/webhook/mock",
            json={
                "user_id": "test_user",
                "user_name": "Test",
                "message_id": "msg_1",
                "text": "Hello"
            }
        )
        assert response.status_code == 200
        
        # 2. Get conversations
        response = await client.get(f"{BASE_URL}/conversations")
        assert response.status_code == 200
        convs = response.json()
        assert len(convs) > 0
        
        # 3. Assume conversation
        conv = convs[0]
        response = await client.post(
            f"{BASE_URL}/conversations/{conv['channel']}/{conv['user_id']}/assume",
            json={"agent_id": "agent_1"}
        )
        assert response.status_code == 200
```

## Manual Testing

### Quick Test Script

```bash
# Make test executable
chmod +x test.sh

# Run tests
./test.sh
```

### Using curl

#### 1. Send Message via Mock Channel
```bash
curl -X POST http://localhost:8000/api/webhook/mock \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_001",
    "user_name": "Alice",
    "message_id": "msg_001",
    "text": "Hi, can you help me?"
  }'
```

#### 2. List Conversations
```bash
curl http://localhost:8000/api/conversations | jq
```

#### 3. Assume Conversation
```bash
curl -X POST http://localhost:8000/api/conversations/mock/user_001/assume \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_1"}'
```

#### 4. Send Agent Reply
```bash
curl -X POST http://localhost:8000/api/conversations/mock/user_001/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Of course! How can I help?"}' \
  -G -d "agent_id=agent_1"
```

#### 5. Close Conversation
```bash
curl -X POST http://localhost:8000/api/conversations/mock/user_001/close \
  -H "Content-Type: application/json" \
  -d '{"message": "Thanks for contacting us!"}'
```

### WebSocket Testing

Using WebSocket CLI:

```bash
# Install wscat (npm install -g wscat)
wscat -c ws://localhost:8000/ws/conversations

# In the WebSocket connection:
{"type": "register_agent", "agent_id": "agent_1"}
{"type": "ping"}

# You'll receive real-time events
```

## Load Testing

### Using Apache Bench

```bash
# Test health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test conversation retrieval
ab -n 1000 -c 10 http://localhost:8000/api/conversations
```

### Using Locust

Create `locustfile.py`:

```python
from locust import HttpUser, task, between
import random

class DashboardUser(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def get_conversations(self):
        self.client.get("/api/conversations")
    
    @task(1)
    def send_message(self):
        user_id = f"user_{random.randint(1, 100)}"
        self.client.post(
            f"/api/webhook/mock",
            json={
                "user_id": user_id,
                "user_name": "Test",
                "message_id": f"msg_{random.randint(1, 10000)}",
                "text": "Test message"
            }
        )
```

Run with:
```bash
locust -f locustfile.py --host=http://localhost:8000
```

## Performance Testing

### Measure Response Times

```python
import time
import httpx

async def measure_performance():
    async with httpx.AsyncClient() as client:
        # Test conversation retrieval
        start = time.time()
        response = await client.get("http://localhost:8000/api/conversations")
        duration = time.time() - start
        
        print(f"Conversations endpoint: {duration*1000:.2f}ms")
        assert duration < 0.5  # Should be under 500ms
```

## End-to-End Testing

### Browser Testing Scenario

1. **Open Dashboard**
   - Visit http://localhost:3000
   - Should load without errors

2. **Send Test Message**
   ```bash
   curl -X POST http://localhost:8000/api/webhook/mock \
     -H "Content-Type: application/json" \
     -d '{
       "user_id": "e2e_test_user",
       "user_name": "E2E Test User",
       "message_id": "e2e_msg_1",
       "text": "E2E Test Message"
     }'
   ```

3. **Verify in Dashboard**
   - Message appears in list
   - Can click to open conversation
   - Can see message history

4. **Assume Conversation**
   - Click "Assume" button
   - Conversation status changes to "HUMAN_ACTIVE"
   - Agent name appears in conversation

5. **Send Reply**
   - Type message in input
   - Click send
   - Message appears immediately
   - WebSocket updates in real-time

6. **Close Conversation**
   - Click menu (three dots)
   - Click "Close Conversation"
   - Conversation status changes to "CLOSED"

## Redis Testing

### Check Redis Data

```bash
# Connect to Redis
docker exec -it handoff_redis redis-cli

# Check keys
KEYS "conversation:*"
KEYS "messages:*"

# Get conversation
GET "conversation:mock:user_001"

# Get message count
LLEN "messages:mock:user_001"

# Get recent messages
LRANGE "messages:mock:user_001" 0 10

# Clear test data (be careful!)
FLUSHDB
```

## Debugging

### Enable Debug Logging

```python
# In app/main.py
import logging

logging.basicConfig(level=logging.DEBUG)
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

### Debug API Requests

```python
import httpx
import logging

httpx.AsyncClient(
    timeout=None,
    proxies="http://localhost:8080"  # Point to proxy for inspection
)
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        cd backend
        pytest tests/
```

## Checklist for Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual API tests work
- [ ] Dashboard loads correctly
- [ ] Messages appear in real-time
- [ ] Agent can assume conversation
- [ ] Agent can send messages
- [ ] Messages appear in external system (mock/real)
- [ ] Conversation can be closed
- [ ] WebSocket connects properly
- [ ] No console errors
- [ ] Performance acceptable
- [ ] Load test completes

## Common Issues

### Tests Timeout
```bash
# Increase timeout in tests
pytest --timeout=60
```

### Redis Connection Error
```bash
# Check Redis is running
docker exec handoff_redis redis-cli ping

# Restart Redis
docker-compose restart redis
```

### WebSocket Tests Fail
```bash
# Check WebSocket logs
docker-compose logs api | grep "websocket"

# Verify connection
wscat -c ws://localhost:8000/ws/conversations
```

## Best Practices

1. **Test as you develop** - Don't leave all testing for the end
2. **Test edge cases** - Empty messages, special characters, etc.
3. **Test error scenarios** - Network failures, malformed data
4. **Automate tests** - Use CI/CD for consistency
5. **Keep tests fast** - Mock external dependencies
6. **Clear test data** - Clean up after tests
