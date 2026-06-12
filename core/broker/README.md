# broker

Event pub/sub 모듈. ([[ADR-004] 인메모리 우선 인프라 채택](/docs/ADR/%5BADR-004%5D%20인메모리%20우선%20인프라%20채택.md))

- 이벤트명으로 receiver를 데코레이터 등록하고, publish 시 등록된 receiver들을 동시 실행한다.
- 인메모리 자체 구현이며, 처리 중 이벤트 수를 추적해 graceful shutdown 판단에 쓴다.
- 실패 처리 수준은 [[ADR-005] 데이터 정합성 수준 채택](/docs/ADR/%5BADR-005%5D%20데이터%20정합성%20수준%20채택.md)을 따른다.
