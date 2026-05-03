#!/bin/bash
# Quick setup script for local development

echo "🚀 Setting up Channel-Agnostic Handoff Dashboard..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Setup backend env
echo ""
echo "📝 Setting up backend environment..."
if [ ! -f "backend/.env" ]; then
    cp backend/.env.example backend/.env
    echo "✅ Created backend/.env (using defaults)"
else
    echo "✅ backend/.env already exists"
fi

# Build and start services
echo ""
echo "🐳 Starting Docker services..."
docker-compose up -d --build

# Wait for services to be ready
echo ""
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo ""
echo "🔍 Checking service health..."

# Check API
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API is running on http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
else
    echo "❌ API is not responding. Check logs: docker-compose logs api"
fi

# Check Frontend
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "⏳ Frontend is starting (may take a moment)..."
fi

# Check Redis
if docker exec handoff_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis is running on localhost:6379"
else
    echo "❌ Redis is not responding. Check logs: docker-compose logs redis"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📚 Quick start guide:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Send a test message:"
echo '   curl -X POST http://localhost:8000/api/webhook/mock \'
echo '     -H "Content-Type: application/json" \'
echo "     -d '{\"user_id\": \"test_user\", \"user_name\": \"Test User\", \"message_id\": \"msg_1\", \"text\": \"Hello!\"}'"
echo "3. Watch the message appear in the dashboard"
echo ""
echo "📖 Documentation: see README.md"
echo "🛑 To stop: docker-compose down"
echo "📊 View logs: docker-compose logs -f"
