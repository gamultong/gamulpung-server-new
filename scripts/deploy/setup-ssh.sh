#!/bin/bash
# Setup SSH key for authentication
set -euo pipefail

# Validate required environment variable
: "${SSH_KEY_B64:?ERROR: SSH_KEY_B64 is required}"

echo "🔑 Setting up SSH key..."

# Create .ssh directory with correct permissions
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Decode and save SSH private key
echo "${SSH_KEY_B64}" | base64 -d > ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

echo "✅ SSH key configured"
