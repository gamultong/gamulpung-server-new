# Gamulung Server

이는 Gamulpung의 Server입니다.

## Introduce
Gamulpung은 지뢰찾기 온라인입니다.
다수의 사람들과 무한한 크기에 맵에서 지뢰찾기를 즐겨보세요.

## 개발 환경 설정

이 프로젝트는 [uv](https://github.com/astral-sh/uv)를 사용하여 의존성을 관리합니다.

### uv 설치

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 의존성 설치

```bash
# 모든 의존성 설치 (프로덕션 + 개발)
uv sync

# 프로덕션 의존성만 설치
uv sync --no-dev

# 개발 의존성 포함
uv sync --dev
```

### 애플리케이션 실행

```bash
# uv를 통해 실행
uv run python main.py

# 또는 직접 실행
python main.py
```

## 문서
Gamulpung Server의 관한 문서는 `/docs`에 정의되어 있습니다.