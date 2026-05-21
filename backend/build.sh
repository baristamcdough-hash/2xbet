#!/usr/bin/env bash
# Render build script for 2xBet backend
set -o errexit

echo "=== Installing dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Initializing database ==="
python init_db.py

echo "=== Build complete ==="
