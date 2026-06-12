# payload

Event에 실리는 payload를 정의하는 모듈.

- 내부 payload: 식별자 중심(IdPayload 계열). 현재 상태는 Receiver가 fetch하고, fetch로 복원 불가능한 변경 이전 snapshot만 함께 싣는다. ([HR 구현 가이드](/docs/Other/Convention%20guide/HR.md))
- 외부 payload: 클라이언트와 주고받는 메시지(ClientMessage/ServerMessage)를 external sub-module에 정의한다. ([API 명세](/docs/Other/API_spec/WebSocket/README.md))
