#!/usr/bin/env bash
# ============================================================
#  CloudDrive — one-command public demo launcher (Option B)
#
#  Starts the app on real AWS S3 + a public Cloudflare tunnel, wires the
#  public URL into the app and the S3 CORS rules, and prints your link.
#
#  Usage:   bash demo.sh
#  Stop:    press Ctrl+C  (cleans up both processes)
# ============================================================
set -e
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"

source .venv/bin/activate

BUCKET=$(grep -E '^S3_BUCKET=' .env | cut -d= -f2)
REGION=$(grep -E '^AWS_REGION=' .env | cut -d= -f2)
REGION=${REGION:-us-east-1}

echo "🧹 Cleaning up any previous run..."
pkill -f "cloudflared tunnel" 2>/dev/null || true
pkill -f "uvicorn backend.main" 2>/dev/null || true
sleep 1

# 1. Start the tunnel and grab the public URL it prints.
echo "🌍 Opening public tunnel..."
~/.local/bin/cloudflared tunnel --url http://localhost:8000 --no-autoupdate > tunnel.log 2>&1 &
TUNNEL_PID=$!

PUB=""
for i in $(seq 1 20); do
  PUB=$(grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" tunnel.log | head -1 || true)
  [ -n "$PUB" ] && break
  sleep 1
done

if [ -z "$PUB" ]; then
  echo "❌ Could not get a tunnel URL. Check tunnel.log"
  kill $TUNNEL_PID 2>/dev/null || true
  exit 1
fi

# 2. Point the app at the public URL (so share links use it).
sed -i "s|^PUBLIC_API_URL=.*|PUBLIC_API_URL=$PUB|" .env

# 3. Allow the public origin to upload directly to S3 (CORS).
if [ -n "$BUCKET" ]; then
  echo "🔐 Updating S3 CORS for $BUCKET ..."
  cat > /tmp/cd_cors.json <<EOF
{ "CORSRules": [ {
  "AllowedOrigins": ["http://localhost:8000","http://127.0.0.1:8000","$PUB"],
  "AllowedMethods": ["GET","PUT","HEAD"],
  "AllowedHeaders": ["*"], "ExposeHeaders": ["ETag"], "MaxAgeSeconds": 3000
} ] }
EOF
  aws s3api put-bucket-cors --bucket "$BUCKET" --region "$REGION" \
    --cors-configuration file:///tmp/cd_cors.json 2>/dev/null \
    && echo "   ✅ CORS updated" || echo "   ⚠️  CORS update skipped (check AWS creds)"
fi

# 4. Start the app.
echo "🚀 Starting CloudDrive..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 > server_s3.log 2>&1 &
APP_PID=$!
sleep 4

# Clean shutdown on Ctrl+C
trap 'echo; echo "🛑 Stopping..."; kill $APP_PID $TUNNEL_PID 2>/dev/null || true; exit 0' INT TERM

echo ""
echo "============================================================"
echo "  ✅ CloudDrive is LIVE and public!"
echo ""
echo "     Open this on ANY device (laptop, phone, share it):"
echo "     👉  $PUB"
echo ""
echo "  Storage: real AWS S3  |  Press Ctrl+C to stop"
echo "============================================================"

# Keep running until the user stops it.
wait $APP_PID
