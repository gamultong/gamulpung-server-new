# Observability 아키텍처 개선

> **상태**: Draft
> **작성일**: 2024-12-19

---

## 목적

Event 추적 및 Handler/Receiver 생명주기 기록을 통한 Observability 확보.

---

## 배경

Event 간 인과관계 및 실행 과정 추적 불가능.

---

## 핵심 개념

### Event = obj의 상태 변경 + 도메인 의도

- obj 변경: Handler만 수행
- Event 정의: Data Layer가 관리
- Event 발행: Publisher가 수행

---

## 변경 내용

### 현재

```
Event 수신 → Receiver → Handler → Event 전파
```

Handler와 Receiver가 분리되어 있어 추적 불가능.

### 변경 후

```
Event 수신
→ Receiver (RLife)
→ Caller
→ Handler (HLife)
→ Publisher
→ Event 전파
```

낮은 레벨에서 Handler와 Receiver를 연결하고 Event 연결성을 추가하여 전 과정을 추적 가능하게 함.

코드 레벨 분리는 기존과 동일하게 유지.

---

## 주요 컴포넌트

### HLife (Handler Lifecycle)
- Handler Method 실행마다 생성
- obj 변경 전/후 snapshot 기록
- 발행된 Event 기록
- 시간 정보 기록

### RLife (Receiver Lifecycle)
- Receiver 실행 전체 추적
- Triggering Event 정보 기록
- HLife 실행 결과 포함
- Receiver 실행 결과 기록
- 시간 정보 기록

### Caller
- Receiver와 triggering Event 보유
- Handler Method 호출 관리
- Event 인과관계 추적에 활용

### Publisher
- HLife의 snapshot diff 분석
- Data Layer의 Event 정의 적용
- Event 발행

---

## Snapshot 처리

### HLife의 snapshot
- Old/new snapshot 기록
- Event 발행 판단에 사용
- Observability 로깅에 사용

### Event payload
- 기존과 동일 (old snapshot 또는 id만 포함)
- New snapshot은 Event에 포함되지 않음

---

## Event 정의 분리

Event 발행 규칙을 Data Layer에서 중앙 관리.

---

## 단계적 마이그레이션

1. Event 정의 이동: Data Layer에 Event 정의 구조 구축
2. Lifecycle 적용: HLife, RLife로 실행 추적 및 로깅
3. Caller 도입: Handler 호출 방식 명시화 및 로깅
4. Publisher 전환: Event 발행 책임 이동 및 로깅
5. Event 관계 정보 추가: Event에 인과관계 메타데이터 추가 및 로깅

각 단계마다 가능한 범위에서 로깅 구현.

---

## 참고

- [[RFC-002] HR Architecture](/docs/RFC/[RFC-002]%20HR%20Architecture.md)
- [handler](/docs/Glossary/dev/handler.md)
- [receiver](/docs/Glossary/dev/receiver.md)
- [event](/docs/Glossary/dev/event.md)
