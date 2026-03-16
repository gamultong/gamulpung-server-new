# Lifecycle Metrics

## 목적
LifeCycle(RLife, HLife) 실행 정보를 Prometheus 메트릭으로 수집하고 Grafana로 시각화한다.

## 구성요소

### LifecycleMetrics
- 위치: [core/lifecycle/metrics/internal/collector.py](/core/lifecycle/metrics/internal/collector.py)
- Prometheus Counter, Histogram, Gauge 정의
- RLife/HLife 시작/종료 시 메트릭 기록

### 훅 연동
- [RLife](/core/lifecycle/internal/rlife.py): `on_enter`/`on_exit`에서 메트릭 수집
- [HLife](/core/lifecycle/internal/hlife.py): `on_enter`/`on_exit`에서 메트릭 수집

### 엔드포인트
- [server.py](/server.py): `/metrics` 라우트로 Prometheus 형식 노출

## 수집 메트릭

| 메트릭 | 타입 | 라벨 | 설명 |
|--------|------|------|------|
| `lifecycle_rlife_duration_seconds` | Histogram | `event`, `receiver` | RLife 실행 시간 |
| `lifecycle_rlife_total` | Counter | `event`, `receiver` | RLife 호출 횟수 |
| `lifecycle_hlife_duration_seconds` | Histogram | `handler`, `method` | HLife 실행 시간 |
| `lifecycle_hlife_total` | Counter | `handler`, `method` | HLife 호출 횟수 |
| `lifecycle_active` | Gauge | `type` | 현재 실행 중인 LifeCycle 수 |

### 라벨 형식
- `event`: scope 포함 (예: `EXTERNAL.CLIENT.MOVE`)
- `receiver`: Receiver 함수명
- `handler`: Handler 클래스명
- `method`: 메서드명
- `type`: `RLife` 또는 `HLife`

## 개발 환경 실행

### 1. 앱 실행
```bash
uv run python main.py
```

### 2. Prometheus + Grafana 실행
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### 3. 접속
- 앱: http://localhost:8000
- 메트릭: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### 4. 종료
```bash
docker-compose -f docker-compose.dev.yml down
```

## Grafana 설정

1. Grafana 접속 (http://localhost:3000)
2. Configuration > Data Sources > Add data source
3. Prometheus 선택
4. URL: `http://prometheus:9090`
5. Save & Test

## 쿼리 예시

### RLife 호출 횟수 (이벤트별)
```promql
sum by (event) (lifecycle_rlife_total)
```

### RLife 평균 실행 시간
```promql
rate(lifecycle_rlife_duration_seconds_sum[5m]) / rate(lifecycle_rlife_duration_seconds_count[5m])
```

### HLife 호출 횟수 (핸들러별)
```promql
sum by (handler) (lifecycle_hlife_total)
```

### 현재 활성 LifeCycle
```promql
lifecycle_active
```

## 관련 문서
- [RFC-002 HR Architecture](/docs/RFC/[RFC-002]%20HR%20Architecture.md)
- [Lifecycle Profiler](/docs/Draft/Lifecycle%20Profiler.md)
