#!/bin/bash
# Main deployment orchestration script
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🎯 Starting deployment orchestration..."

# Cleanup function
cleanup() {
  if [ -f /tmp/tunnel.pid ]; then
    TUNNEL_PID=$(cat /tmp/tunnel.pid)
    echo "🧹 Cleaning up tunnel (PID: ${TUNNEL_PID})..."
    kill "${TUNNEL_PID}" 2>/dev/null || true
    rm -f /tmp/tunnel.pid
  fi
}
trap cleanup EXIT

# Execute deployment steps
"${SCRIPT_DIR}/setup-tunnel.sh"
"${SCRIPT_DIR}/setup-ssh.sh"
"${SCRIPT_DIR}/transfer-files.sh"
"${SCRIPT_DIR}/execute-deploy.sh"

echo "🎉 Deployment orchestration completed!"
