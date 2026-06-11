#!/bin/bash
# Execute deployment on remote server
set -euo pipefail

# Validate required environment variables
: "${SSH_USERNAME:?ERROR: SSH_USERNAME is required}"
: "${DOCKER_USERNAME:?ERROR: DOCKER_USERNAME is required}"
: "${DOCKER_REPONAME:?ERROR: DOCKER_REPONAME is required}"
: "${DOCKER_TAG:?ERROR: DOCKER_TAG is required}"
: "${ENVIRONMENT:?ERROR: ENVIRONMENT is required}"
: "${CONTAINER_NAME:?ERROR: CONTAINER_NAME is required}"
: "${CONTAINER_PORT_MAPPING:=8000:8000}"

# SSH connection options
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 2222"
REMOTE_HOST="${SSH_USERNAME}@localhost"

echo "🚀 Executing deployment on remote server..."
echo "Environment: ${ENVIRONMENT}"
echo "Docker Tag: ${DOCKER_TAG}"

# Execute deploy.sh on remote server
ssh ${SSH_OPTS} "${REMOTE_HOST}" \
  "DOCKER_TAG='${DOCKER_TAG}' \
   ENVIRONMENT='${ENVIRONMENT}' \
   DOCKER_USERNAME='${DOCKER_USERNAME}' \
   DOCKER_REPONAME='${DOCKER_REPONAME}' \
   CONTAINER_NAME='${CONTAINER_NAME}' \
   CONTAINER_PORT_MAPPING='${CONTAINER_PORT_MAPPING}' \
   CONTAINER_MEMORY_LIMIT='${CONTAINER_MEMORY_LIMIT:-}' \
   bash ~/deploy.sh"

echo "✅ Deployment executed successfully"
