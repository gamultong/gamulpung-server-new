## 정의
obj의 state 변화. event 정의에는 domain logic이 반영된다. ([[RFC-002] HR Architecture](/docs/RFC/%5BRFC-002%5D%20HR%20Architecture.md))

## scope
event는 4개 scope로 분류되며 `data/event`에 정의된다.
- `ClientEvent`: 클라이언트가 서버로 보내는 event. external receiver가 소비한다.
- `ServerEvent`: 서버가 클라이언트로 보내는 event.
- `InternalEvent`: 서버 내부 통지용 event. internal receiver가 소비한다.
- `TriggerEvent`: 서버 내부 동작 유발용 event. trigger receiver가 소비한다.

이름은 대문자+하이픈으로 강제된다 (예: OPEN-TILES). ([명명 규칙](/docs/Other/API_spec/WebSocket/README.md))
