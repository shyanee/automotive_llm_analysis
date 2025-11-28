#!/bin/sh

set -e
set -o pipefail

# Check for 'uv' (as it's a hard requirement)
if ! command -v uv >/dev/null 2>&1; then
    echo "Error: 'uv' command not found. Please install uv first." >&2
    exit 1
fi

# 1. Initialise and Sync Venv
if [ ! -d "venv" ]; then
    echo "Creating new virtual environment..."
    uv venv venv
    . venv/bin/activate
    uv pip install -r requirements.txt -q
else 
    echo "Syncing existing virtual environment..."
    # Activate for consistency, especially if other python commands will follow
    . venv/bin/activate
    uv pip sync requirements.txt -q
fi

# Gemini API
uv pip install -q -U google-genai 

# 2. Create .env file if it doesn't exist
[ ! -f .env ] && echo "GOOGLE_API_KEY=" > .env || true

# 3. Create project folders
mkdir -p data output/logs output/plots

echo "Setup complete. The environment is ready."