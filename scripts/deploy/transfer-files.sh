#!/bin/bash
# Transfer deployment files to remote server via SCP
set -euo pipefail

# Validate required environment variables
: "${SSH_USERNAME:?ERROR: SSH_USERNAME is required}"

# SSH connection options
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P 2222"
REMOTE_HOST="${SSH_USERNAME}@localhost"

echo "📤 Transferring files to ${REMOTE_HOST}..."

# Transfer server-deploy.sh
echo "  - Copying server-deploy.sh..."
scp ${SSH_OPTS} \
  scripts/deploy/server-deploy.sh \
  "${REMOTE_HOST}:~/deploy.sh"

# Transfer .env file
echo "  - Copying .env..."
scp ${SSH_OPTS} \
  .env \
  "${REMOTE_HOST}:~/.env"

echo "✅ Files transferred successfully"
