#!/bin/bash

# FOIA-Buddy Streamlit App Launcher
# Easy launch script for the Streamlit dashboard

echo "🚀 Launching FOIA-Buddy Streamlit Dashboard..."
echo ""
echo "Make sure you have set your NVIDIA API key:"
echo "  export NVIDIA_API_KEY=\"your_key_here\""
echo ""

# Check if NVIDIA_API_KEY is set
if [ -z "$NVIDIA_API_KEY" ]; then
    echo "⚠️  Warning: NVIDIA_API_KEY environment variable is not set"
    echo "   You can enter it in the dashboard sidebar"
    echo ""
fi

# Launch Streamlit
streamlit run foia_buddy/streamlit_app.py \
    --server.headless=false \
    --server.port=8501 \
    --browser.gatherUsageStats=false \
    --theme.primaryColor="#76B900" \
    --theme.backgroundColor="#FFFFFF" \
    --theme.secondaryBackgroundColor="#F0F2F6" \
    --theme.textColor="#262730"

