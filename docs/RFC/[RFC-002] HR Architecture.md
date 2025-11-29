Gamulpung Server의 이벤트 기반 아키텍처를 정의합니다.

<!-- TODO: ADR-003 작성 권장 - HR 아키텍처 채택 이유 (기존 아키텍처의 Event 복잡도 문제 및 논의 사항) -->

## 개요
HR은 Handler-Receiver의 약자입니다.
Event 기반의 아키텍처로 Handler와 Receiver의 상호작용으로 동작합니다.

Event의 발행과 소비 주체를 명확히하며, Handler -> Receiver의 단방향 Event Flow를 구축합니다.

## Layer
HR은 크게 3가지 Layer를 가집니다:
- DataLayer : Data, Event 정의
- HandlerLayer : obj, Handler 정의
- ReceiverLayer : Receiver 정의

Layer의 의존관계는 다음과 같습니다:
![alt text](img/1-1.png)
