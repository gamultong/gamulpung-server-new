#!/bin/bash
# Setup SSH key for authentication
set -euo pipefail

# Validate required environment variable
: "${SSH_KEY_B64:?ERROR: SSH_KEY_B64 is required}"

echo "🔑 Setting up SSH key..."
echo "DEBUG: SSH_KEY_B64 length: ${#SSH_KEY_B64}"

# Create .ssh directory with correct permissions
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Decode and save SSH private key
if ! echo "${SSH_KEY_B64}" | base64 -d > ~/.ssh/id_rsa 2>/dev/null; then
  echo "❌ ERROR: Failed to decode SSH_KEY_B64. Please check if it's valid base64."
  exit 1
fi
chmod 600 ~/.ssh/id_rsa

echo "✅ SSH key configured"
