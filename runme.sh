#!/bin/sh

set -e  # Exit on error
set -o pipefail

uv venv venv
. venv/bin/activate

echo "Upgrading pip..."
uv pip install --upgrade pip setuptools wheel
uv pip install -r requirements.txt

uv pip install -q -U google-genai
