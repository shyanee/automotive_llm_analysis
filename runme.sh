#!/bin/sh

set -e  # Exit on error
set -o pipefail

# Initialise venv
if [ ! -d "venv" ]; then
    uv venv venv
fi

. venv/bin/activate

# Install package dependencies
echo "Installing package dependencies"
uv pip install -r requirements.txt
# uv pip sync requirements.txt

# LLM
uv pip install -q -U google-genai

# Create .env
[ ! -f .env ] && echo "GOOGLE_API_KEY=" > .env || true