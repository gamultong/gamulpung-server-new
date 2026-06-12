# Lifecycle

## 목적
Handler와 Receiver의 함수 실행을 관리하는 공통 플랫폼을 정의한다. 상태 snapshot과 Event 캡처처럼 함수 안에 반복되던 처리를 플랫폼이 흡수해 보일러플레이트를 제거하고, Observability(메트릭·프로파일)는 이 플랫폼 위에 기능으로 올린다. ([초안](/docs/Other/Draft/2단계-Lifecycle%20적용.md), [설계 문답](/docs/Other/Design%20QnA%202026-06.md))

## 규칙
- Lifecycle은 core에 정의하며 broker와 직교한다 (상호 import 없음).
- 실행 주체별로 두 종류를 사용한다.
    - HLife: Handler 메서드의 실행 추적. before/after snapshot과 발행 Event를 기록한다.
    - RLife: Receiver 함수의 실행 추적.
- 적용은 데코레이터 방식으로 하며, 추적 대상 식별자(Handler명·메서드명)를 함께 기록한다.
- 함수 내부(inline)에서 현재 Lifecycle에 접근해 snapshot·Event를 기록한다. 반환값·파라미터를 통한 전달은 시점이 고정되고 함수 인터페이스를 오염시키므로 쓰지 않는다.
- RLife 컨텍스트 안에서 실행된 HLife는 Caller에 자동 등록되어 호출 관계가 추적된다.
- 실행 기록은 메트릭(Prometheus)과 프로파일(Chrome Trace)로 수집한다. ([초안](/docs/Other/Draft/Lifecycle%20Metrics.md))

## 적용 범위
[[RFC-002] HR Architecture](/docs/RFC/%5BRFC-002%5D%20HR%20Architecture.md)의 모든 Handler 변이 메서드와 모든 Receiver에 적용된다.
