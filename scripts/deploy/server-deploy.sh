#!/bin/bash

set -e  # 에러 발생 시 즉시 종료

# 환경변수 검증
required_vars=("DOCKER_USERNAME" "DOCKER_REPONAME" "DOCKER_TAG" "ENVIRONMENT" "CONTAINER_NAME")
for var in "${required_vars[@]}"; do
  if [ -z "${!var}" ]; then
    echo "❌ ERROR: Required environment variable $var is not set"
    exit 1
  fi
done

CONTAINER_PORT_MAPPING="${CONTAINER_PORT_MAPPING:-8000:8000}"

echo "🚀 Starting deployment for $ENVIRONMENT environment"
echo "📦 Image: $DOCKER_USERNAME/$DOCKER_REPONAME:$DOCKER_TAG"
echo "🐳 Container: $CONTAINER_NAME"
echo "🔌 Port: $CONTAINER_PORT_MAPPING"

# Memory limit (optional)
MEMORY_ARGS=()
if [ -n "${CONTAINER_MEMORY_LIMIT:-}" ]; then
  MEMORY_ARGS+=(--memory "${CONTAINER_MEMORY_LIMIT}")
  echo "💾 Memory limit: ${CONTAINER_MEMORY_LIMIT}"
fi

# Docker 설치 확인 및 설치
if ! type docker > /dev/null 2>&1; then
  echo "📥 Docker not found. Installing..."
  sudo apt-get update
  sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
  sudo apt update
  sudo apt install -y docker-ce
  echo "✅ Docker installed successfully"
fi

# 환경변수로 이미지명 구성
IMAGE_NAME="${DOCKER_USERNAME}/${DOCKER_REPONAME}:${DOCKER_TAG}"
ENV_FILE_PATH=".env"
VOLUME_MOUNT_PATH="/var/lib/gamulpung"


# 기존 컨테이너 제거
if sudo docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "🗑️  Removing existing container: $CONTAINER_NAME"
  sudo docker rm -f "$CONTAINER_NAME"
  # Wait for port to be released
  sleep 2
fi

# 기존 이미지 제거
if sudo docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}$"; then
  echo "🗑️  Removing old image: $IMAGE_NAME"
  sudo docker rmi "$IMAGE_NAME"
fi

# 새 이미지 pull 및 실행
echo "📥 Pulling new image: $IMAGE_NAME"
sudo docker pull "$IMAGE_NAME"

echo "📂 Current dir: $(pwd)"

ENV_ARGS=()
if [ -f "$ENV_FILE_PATH" ]; then
  echo "📄 Loading env from $ENV_FILE_PATH"
  while IFS= read -r line; do
    # 빈 줄 / 주석은 스킵
    [ -z "$line" ] && continue
    case "$line" in
      \#*) continue ;;
    esac

    # KEY=VALUE 형태 그대로 --env 옵션으로 추가
    ENV_ARGS+=(--env "$line")
  done < "$ENV_FILE_PATH"
else
  echo "⚠️ $ENV_FILE_PATH 파일이 없습니다. env 없이 컨테이너를 실행합니다."
fi

echo "🚀 Starting container: $CONTAINER_NAME"
sudo docker run -d \
  -p "$CONTAINER_PORT_MAPPING" \
  -v "$PWD:$VOLUME_MOUNT_PATH" \
  --restart unless-stopped \
  "${MEMORY_ARGS[@]}" \
  "${ENV_ARGS[@]}" \
  --name "$CONTAINER_NAME" \
  "$IMAGE_NAME"

echo "✅ Deployment completed successfully!"
echo "📊 Container status:"
sudo docker ps --filter "name=$CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
