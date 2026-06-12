# HR Architecture

## 목적
Event 기반 아키텍처를 통해 발행/소비 주체를 명확히 분리하고 단방향 Event Flow를 구축한다.

## 규칙
- HR은 `Handler-Receiver` 패턴을 따른다.
- Event Flow는 Handler -> Receiver 단방향으로 흐른다.
- 3개 Layer로 구성된다: DataLayer, HandlerLayer, ReceiverLayer
- Layer 의존관계: ReceiverLayer -> HandlerLayer -> DataLayer

![Layer 의존관계](/docs/RFC/img/1-1.png)

### Layer 정의
- DataLayer: Data, Event 정의
- HandlerLayer: obj, Handler 정의
- ReceiverLayer: Receiver 정의

## 적용 범위
프로젝트 전체 아키텍처에 적용된다.

## 관련 문서
- 실행 추적: [[RFC-008] Lifecycle](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md)
- Event 발행 규칙: [[RFC-009] Emitter](/docs/RFC/%5BRFC-009%5D%20Emitter.md)
