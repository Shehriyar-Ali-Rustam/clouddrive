#!/usr/bin/env bash
# ------------------------------------------------------------
#  CloudDrive — one-command local launcher
# ------------------------------------------------------------
set -e
cd "$(dirname "$0")"

# 1. virtual env
if [ ! -d ".venv" ]; then
  echo "📦 Creating virtual environment..."
  python3 -m venv .venv
fi
source .venv/bin/activate

# 2. dependencies
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 3. config
if [ ! -f ".env" ]; then
  echo "⚙️  Creating .env from template..."
  cp .env.example .env
fi

# 4. run
echo ""
echo "🚀 CloudDrive running at  http://localhost:8000"
echo "   (Ctrl+C to stop)"
echo ""
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
