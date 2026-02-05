# Observability

프로젝트의 관찰성(Observability) 설정 및 도구에 대한 문서.

## 구성 요소

### Prometheus
메트릭 수집 및 저장.
- 포트: 9090
- 설정: [docker-compose.dev.yml](/docker-compose.dev.yml)

### Grafana
메트릭 시각화 대시보드.
- 포트: 3000
- 계정: admin / admin
- 설정: [docker-compose.dev.yml](/docker-compose.dev.yml)

### Grafana MCP 서버
AI 어시스턴트가 Grafana에 접근할 수 있도록 하는 MCP(Model Context Protocol) 서버.

#### 설치 위치
- 바이너리: `bin/mcp-grafana`
- 설정 파일: `.env.grafana-mcp`

#### 실행 방법
```bash
# 환경 변수 설정 후 실행
export GRAFANA_URL=http://host.docker.internal:3000
export GRAFANA_USERNAME=admin
export GRAFANA_PASSWORD=admin

# SSE 모드로 실행 (백그라운드)
./bin/mcp-grafana -transport sse -address localhost:8001 &

# stdio 모드로 실행 (대화형)
./bin/mcp-grafana
```

#### 주요 기능
- 대시보드 검색/조회/생성/수정
- Prometheus PromQL 쿼리 실행
- 알림 규칙 관리
- 인시던트 생성/관리

#### 참고
- [GitHub - grafana/mcp-grafana](https://github.com/grafana/mcp-grafana)
- 버전: v0.9.0

## 실행

```bash
# Prometheus + Grafana 시작
docker-compose -f docker-compose.dev.yml up -d

# 서버 메트릭 엔드포인트
# http://localhost:8000/metrics
```

## 대시보드

### LifeCycle Metrics
RLife, HLife 호출 횟수 및 지연 시간 모니터링.
- UID: `lifecycle-metrics`
- 패널:
  - RLife Total Calls
  - HLife Total Calls
  - RLife Calls per Minute (by Event)
  - HLife p95 Latency (by Handler)
