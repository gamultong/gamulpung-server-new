# HR Architecture 채택 배경

## 상황
domain logic과 state가 한 곳에 섞이면 코드가 다루기는 쉬워도(easy) 단순하지(simple) 않게 되어, 복잡성이 누적되는 문제가 있었다.

## 결정
state 관리와 domain logic을 분리하는 Handler-Receiver 구조를 채택한다. state는 Handler가 관리하고, Receiver는 state 없는 domain logic만 수행한다. ([[RFC-002] HR Architecture](/docs/RFC/%5BRFC-002%5D%20HR%20Architecture.md))

## 근거(요약)
- 프로그램의 복잡성은 state에서 온다.
- domain logic에서 state를 제거하면 로직이 단순해지고 추론이 쉬워진다.
- Event 기반 단방향 흐름으로 발행 주체(Handler)와 소비 주체(Receiver)가 명확히 분리된다. ([원문 답변](/docs/Other/Design%20QnA%202026-06.md))
