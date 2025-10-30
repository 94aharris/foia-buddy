#!/bin/bash

# FOIA-Buddy V2 Launch Script

echo "🤖 FOIA-Buddy V2 - Multi-Agent Demo"
echo "===================================="
echo ""

# Check if NVIDIA_API_KEY is set
if [ -z "$NVIDIA_API_KEY" ]; then
    echo "⚠️  Warning: NVIDIA_API_KEY environment variable not set"
    echo "You can set it with: export NVIDIA_API_KEY='your_key_here'"
    echo "Or enter it in the app sidebar"
    echo ""
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python -c "import streamlit" &> /dev/null; then
    echo "❌ Streamlit not found. Installing dependencies..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies OK"
fi

echo ""
echo "🚀 Launching FOIA-Buddy V2..."
echo "The app will open at http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run streamlit
streamlit run app.py
