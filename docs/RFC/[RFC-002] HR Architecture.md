# HR Architecture

## 목적
Event 기반 아키텍처를 통해 발행/소비 주체를 명확히 분리하고 단방향 Event Flow를 구축한다. ([[ADR-003] HR Architecture 채택 배경](/docs/ADR/%5BADR-003%5D%20HR%20Architecture%20채택%20배경.md))

## 규칙
- HR은 `Handler-Receiver` 패턴을 따른다.
- Event Flow는 Handler -> Receiver 단방향으로 흐른다.
- 3개 Layer로 구성된다: DataLayer, HandlerLayer, ReceiverLayer
- Layer 의존관계: ReceiverLayer -> HandlerLayer -> DataLayer
- Handler·Receiver의 실행 추적은 [[RFC-008] Lifecycle](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md)을 따른다.
- Handler·Receiver의 작성 규칙은 [HR 구현 가이드](/docs/Other/Convention%20guide/HR.md)를 따른다.

![Layer 의존관계](/docs/RFC/img/1-1.png)

### Layer 정의
- DataLayer: Data, Event 정의 (Event 발행 규칙: [[RFC-009] Emitter](/docs/RFC/%5BRFC-009%5D%20Emitter.md))
- HandlerLayer: obj, Handler 정의
- ReceiverLayer: Receiver 정의

## 적용 범위
프로젝트 전체 아키텍처에 적용된다.
