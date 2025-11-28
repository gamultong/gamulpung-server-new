#!/bin/bash
# Setup Cloudflare Tunnel for SSH access
set -euo pipefail

# Validate required environment variables
: "${CLOUDFLARE_TUNNEL_HOSTNAME:?ERROR: CLOUDFLARE_TUNNEL_HOSTNAME is required}"
: "${CF_ACCESS_CLIENT_ID:?ERROR: CF_ACCESS_CLIENT_ID is required}"
: "${CF_ACCESS_CLIENT_SECRET:?ERROR: CF_ACCESS_CLIENT_SECRET is required}"

echo "🔧 Setting up Cloudflare Tunnel..."
echo "Hostname: ${CLOUDFLARE_TUNNEL_HOSTNAME}"

# Install cloudflared if not exists
if ! command -v cloudflared &> /dev/null; then
  echo "📥 Installing cloudflared..."
  curl -L --output cloudflared.deb \
    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
  sudo dpkg -i cloudflared.deb
  rm -f cloudflared.deb
fi

# Start tunnel in background
cloudflared access tcp \
  --hostname "${CLOUDFLARE_TUNNEL_HOSTNAME}" \
  --url localhost:2222 \
  --service-token-id "${CF_ACCESS_CLIENT_ID}" \
  --service-token-secret "${CF_ACCESS_CLIENT_SECRET}" &

TUNNEL_PID=$!
echo "${TUNNEL_PID}" > /tmp/tunnel.pid

# Wait for tunnel to establish
echo "⏳ Waiting for tunnel to establish..."
sleep 5

echo "✅ Tunnel established (PID: ${TUNNEL_PID})"
