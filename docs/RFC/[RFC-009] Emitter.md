# Emitter

## 목적
Event 발행 규칙(어떤 상태 변화가 어떤 Event를 만드는가)을 Data Layer에서 중앙 관리한다. 상태 변경은 Handler의 일이지만 "변경이 무엇을 의미하는가"의 정의는 Data의 일이므로, Event 도출은 snapshot 비교로 자동화한다. ([초안](/docs/Other/Draft/1단계-Event%20정의%20이동.md), [설계 문답](/docs/Other/Design%20QnA%202026-06.md))

## 규칙
- Emitter는 obj의 data 모듈 하위 emitter sub-module에 정의한다.
- Emitter는 obj의 old/new snapshot을 비교하여 Event 목록을 도출한다.
- 발행 규칙은 데코레이터로 Emitter에 등록한다.
- Emitter는 Event를 만들기만 한다. publish는 Handler가 수행한다. ([[RFC-002] HR Architecture](/docs/RFC/%5BRFC-002%5D%20HR%20Architecture.md)의 'Handler = Event 발행 주체' 규칙)

## 적용 범위
상태 변화로 Event를 발행하는 모든 obj(data)에 적용된다.
