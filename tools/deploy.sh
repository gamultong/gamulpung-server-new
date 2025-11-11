#!/bin/bash

set -e

echo "🚀 시작: Gamulpung 서버 배포"

cd /opt/gamulpung-server

# Git 최신 코드 가져오기
echo "📥 최신 코드 가져오는 중..."
git pull origin main

# Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 중..."
docker build -t gamulpung-server:latest .

# 기존 컨테이너 중지 및 제거
echo "🛑 기존 컨테이너 중지/제거 중..."
docker stop gamulpung-server || true
docker rm gamulpung-server || true

# 새 컨테이너 실행
echo "✅ 새 컨테이너 실행 중..."
docker run -d \
  --name gamulpung-server \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file game.env \
  gamulpung-server:latest

echo "✨ 배포 완료!"
docker ps | grep gamulpung-server
