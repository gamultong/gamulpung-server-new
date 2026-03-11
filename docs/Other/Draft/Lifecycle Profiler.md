# Lifecycle Profiler

## 목적
Lifecycle(RLife, HLife) 실행을 시계열 데이터로 수집하고 시각화한다.

## 구성요소

### LifecycleProfiler
- 위치: [core/lifecycle/internal/profiler.py](/core/lifecycle/internal/profiler.py)
- Context manager로 opt-in 방식 프로파일링
- 스레드 안전: `threading.Lock` 사용
- Chrome Trace 형식 출력 지원

### 훅 연동
- [RLife](/core/lifecycle/internal/rlife.py): `on_enter`/`on_exit`에서 profiler 호출
- [HLife](/core/lifecycle/internal/hlife.py): `on_enter`/`on_exit`에서 profiler 호출

## 사용법

### 기본 사용
```python
from core.lifecycle import LifecycleProfiler

with LifecycleProfiler() as profiler:
    # 시나리오 실행
    ...

# 결과 저장
profiler.save("result.json")
```

### 결과 확인
```python
# 기록 개수
len(profiler.records)

# 개별 기록 조회
for record in profiler.records:
    print(record.name, record.category, record.phase)
```

## 출력 형식
Chrome Trace JSON 형식으로 출력된다.

```json
[
  {
    "name": "join_receiver",
    "cat": "RLife",
    "ph": "B",
    "ts": 211607,
    "pid": 1,
    "tid": 1,
    "args": {"event": "JOIN"}
  }
]
```

필드:
- `name`: Lifecycle 이름
- `cat`: 카테고리 (RLife/HLife)
- `ph`: 페이즈 (B=begin, E=end)
- `ts`: 타임스탬프 (마이크로초)
- `args`: 추가 정보

## 시각화
1. https://ui.perfetto.dev 접속
2. JSON 파일 로드
3. 타임라인 뷰에서 확인

## 테스트
- 위치: [tests/integration/test_lifecycle_profiler.py](/tests/integration/test_lifecycle_profiler.py)
- 실행: `pytest tests/integration/test_lifecycle_profiler.py`

## 관련 문서
- [RFC-002 HR Architecture](/docs/RFC/[RFC-002]%20HR%20Architecture.md)
- [RFC-003 Module](/docs/RFC/[RFC-003]%20Module.md)
