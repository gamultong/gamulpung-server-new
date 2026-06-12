# Emitter

## 목적
Event 발행 규칙(어떤 상태 변화가 어떤 Event를 만드는가)을 Data Layer에서 중앙 관리한다. ([초안](/docs/Other/Draft/1단계-Event%20정의%20이동.md))

## 규칙
- Emitter는 obj의 data 모듈 하위 `emitter/` sub-module에 정의한다.
    - 예: `data/cursor/emitter`, `data/board/emitter`, `data/bomb/emitter`
- Emitter는 old/new snapshot의 diff에서 Event 목록을 도출한다.
    - `get_events(old, new) -> list[Event]`
- 발행 규칙(핸들러 함수)은 데코레이터로 등록한다.
- Emitter는 Event를 만들기만 한다. publish는 Handler가 수행한다 (Handler = Event 발행 주체).

## 적용 범위
상태 변화로 Event를 발행하는 모든 obj(data)에 적용된다.

## 관련 문서
- [[RFC-002] HR Architecture](/docs/RFC/%5BRFC-002%5D%20HR%20Architecture.md)
- [[RFC-008] Lifecycle](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md)
