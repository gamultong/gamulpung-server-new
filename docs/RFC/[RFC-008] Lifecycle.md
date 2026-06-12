# Lifecycle

## 목적
Handler와 Receiver의 실행을 추적·기록하여 Observability를 확보한다. ([초안](/docs/Other/Draft/2단계-Lifecycle%20적용.md))

## 규칙
- Lifecycle은 core에 정의하며 broker와 직교한다 (상호 import 없음).
- 실행 주체별로 두 종류를 사용한다.
    - HLife: Handler 메서드의 실행 추적. before/after snapshot과 발행 Event를 기록한다.
    - RLife: Receiver 함수의 실행 추적.
- 적용은 데코레이터 방식으로 하며, 추적 대상 식별자(Handler명·메서드명)를 함께 기록한다.
- RLife 컨텍스트 안에서 실행된 HLife는 Caller에 자동 등록되어 호출 관계가 추적된다.
- 실행 기록은 메트릭(Prometheus)과 프로파일(Chrome Trace)로 수집한다. ([초안](/docs/Other/Draft/Lifecycle%20Metrics.md))

## 적용 범위
[[RFC-002] HR Architecture](/docs/RFC/%5BRFC-002%5D%20HR%20Architecture.md)의 모든 Handler 변이 메서드와 모든 Receiver에 적용된다.
