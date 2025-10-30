#!/bin/bash

# FOIA-Buddy API Server Startup Script

echo "🚀 Starting FOIA-Buddy API Server..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if NVIDIA_API_KEY is set
if [ -z "$NVIDIA_API_KEY" ]; then
    echo "❌ Error: NVIDIA_API_KEY environment variable is not set"
    echo ""
    echo "Please set your NVIDIA API key:"
    echo "  export NVIDIA_API_KEY='your_key_here'"
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo "⚠️  No virtual environment found. Consider creating one:"
    echo "  python -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
fi

# Set default host and port if not provided
export FOIA_API_HOST=${FOIA_API_HOST:-0.0.0.0}
export FOIA_API_PORT=${FOIA_API_PORT:-8000}

echo "✅ Configuration:"
echo "   Host: $FOIA_API_HOST"
echo "   Port: $FOIA_API_PORT"
echo ""
echo "📚 API Documentation will be available at:"
echo "   http://localhost:$FOIA_API_PORT/docs"
echo ""
echo "🌐 Open frontend_example.html in your browser to use the UI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the server
python -m foia_buddy.server
