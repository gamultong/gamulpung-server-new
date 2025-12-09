FROM python:3.13-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 모든 파일 복사 (의존성 설치를 위해 전체 컨텍스트 필요)
COPY . .

# 프로젝트 설치 (의존성 포함)
RUN uv pip install --system --no-cache .

# 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["python", "main.py"]
