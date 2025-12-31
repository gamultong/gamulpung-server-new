# 2단계 - Lifecycle 적용

## 목적

Handler와 Receiver의 실행을 추적하고 로깅하여 Observability를 확보한다.

---

## 작업

### 1. HLife (Handler Lifecycle) 적용

Handler 메서드 실행 시 before/after snapshot 기록:
- `BoardHandler.togle_flag()`
- `BoardHandler.open_tiles()`
- `CursorHandler.create()`
- `CursorHandler.move()`
- `CursorHandler.death()`
- `CursorHandler.increase_score()`
- `CursorHandler.set_window()`

각 메서드에 `@with_lifecycle` 데코레이터 적용 및 로깅 추가.

### 2. RLife (Receiver Lifecycle) 적용

Receiver 실행 추적:
- External Receiver (Client Event 처리)
- Internal Receiver (Internal Event 처리)

각 receiver 함수에 `@with_lifecycle` 데코레이터 적용 및 로깅 추가.

### 3. 로깅 구현

Lifecycle 정보를 활용한 로깅:
- Handler 실행 시작/종료 로그
- Receiver 실행 시작/종료 로그
- Before/After snapshot 로그 (개발 환경)
- 에러 발생 시 context 정보 포함

---

## 결과

모든 Handler와 Receiver 실행이 추적 가능하고, 로그를 통해 시스템 동작을 관찰할 수 있다.
