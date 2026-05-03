#!/bin/bash
# Test script for the handoff dashboard system

BASE_URL="http://localhost:8000/api"

echo "🧪 Testing Handoff Dashboard API"
echo "=================================="
echo ""

# 1. Check health
echo "1️⃣  Checking API health..."
curl -s $BASE_URL/../health | jq . || echo "❌ Health check failed"
echo ""

# 2. List channels
echo "2️⃣  Listing available channels..."
curl -s $BASE_URL/channels | jq . || echo "❌ Failed to list channels"
echo ""

# 3. Send mock message
echo "3️⃣  Sending test message via mock channel..."
RESPONSE=$(curl -s -X POST $BASE_URL/webhook/mock \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_1",
    "user_name": "Test User 1",
    "message_id": "msg_001",
    "text": "Hello from test!"
  }')
echo $RESPONSE | jq .
echo ""

# 4. Get conversations
echo "4️⃣  Getting all conversations..."
curl -s $BASE_URL/conversations | jq . || echo "❌ Failed to get conversations"
echo ""

# 5. Get specific conversation
echo "5️⃣  Getting specific conversation..."
curl -s $BASE_URL/conversations/mock/test_user_1 | jq . || echo "❌ Failed to get conversation"
echo ""

# 6. Assume conversation
echo "6️⃣  Assigning agent to conversation..."
curl -s -X POST $BASE_URL/conversations/mock/test_user_1/assume \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_1"}' | jq . || echo "❌ Failed to assume conversation"
echo ""

# 7. Send agent message
echo "7️⃣  Sending agent message..."
curl -s -X POST $BASE_URL/conversations/mock/test_user_1/message \
  -H "Content-Type: application/json" \
  -d '{"text": "Hi there! How can I help?"}' \
  -G -d "agent_id=agent_1" | jq . || echo "❌ Failed to send message"
echo ""

# 8. Get updated conversation
echo "8️⃣  Getting updated conversation..."
curl -s $BASE_URL/conversations/mock/test_user_1 | jq . || echo "❌ Failed to get updated conversation"
echo ""

# 9. Close conversation
echo "9️⃣  Closing conversation..."
curl -s -X POST $BASE_URL/conversations/mock/test_user_1/close \
  -H "Content-Type: application/json" \
  -d '{"message": "Thank you for contacting us!"}' | jq . || echo "❌ Failed to close conversation"
echo ""

echo "✅ Testing complete!"
echo ""
echo "📊 Summary:"
echo "- Check API: curl http://localhost:8000/health"
echo "- Check Frontend: http://localhost:3000"
echo "- Check Redis: docker exec handoff_redis redis-cli ping"
