# HR 구현 가이드

[[RFC-002] HR Architecture](/docs/RFC/%5BRFC-002%5D%20HR%20Architecture.md)를 구현할 때 따르는 작성 패턴.

## Receiver
- 1파일 = 1이벤트 = 1함수로 작성한다.
- 파일 상단에 수신 이벤트의 타입 별칭을 선언해, 받는 payload 구조를 자체 문서화한다.
- 등록(broker)과 실행 추적([[RFC-008] Lifecycle](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md)) 데코레이터를 함께 적용한다.
- receiver 디렉토리 분류는 [event](/docs/Glossary/dev/event.md) scope와 1:1 대응한다: external=Client, internal=Internal, trigger=Trigger.
- 도메인 규칙을 위반한 입력은 한국어 warning 로그 후 조기 반환으로 무해화한다. 연결을 끊지 않는다.

## Handler
- [Handler](/docs/Glossary/dev/handler.md)는 obj의 단일 엔트리이며 classmethod로 구성한다.
- 상태 변이 메서드는 동일한 5단계를 따른다.
    1. 실행 추적 시작 ([[RFC-008] Lifecycle](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md))
    2. 이전/이후 snapshot 기록
    3. 상태 갱신
    4. snapshot 비교로 Event 도출 ([[RFC-009] Emitter](/docs/RFC/%5BRFC-009%5D%20Emitter.md))
    5. Event publish
- obj를 외부에 내보낼 때와 저장할 때 모두 복사본을 사용한다. ([data](/docs/Glossary/dev/data.md)는 immutable snapshot)
- Event publish는 Handler만 수행한다.

## Event payload
- payload에는 식별자와, 처리 시점의 fetch로는 복원할 수 없는 정보(변경 이전 snapshot)만 담는다.
- 현재 상태는 Receiver가 처리 시점에 fetch한다. 과거 상태는 fetch로 복원할 수 없으므로 Emitter가 payload에 실어 보낸다.
- 이 분업 덕에 Receiver는 이벤트의 전달 시점·순서에 둔감해진다. ([[ADR-004] 인메모리 우선 인프라 채택](/docs/ADR/%5BADR-004%5D%20인메모리%20우선%20인프라%20채택.md))

## 신뢰 경계
- 클라이언트가 보낸 식별자를 신뢰하지 않는다. 발신자 id는 연결 계층이 단일 지점에서 주입한다.
- 클라이언트 메시지의 형식 오류는 연결 종료가 아니라 경고 후 무시로 처리한다.

## 저장소
- SQL은 storage 모듈 내부의 .sql 파일로만 존재하며, Handler·Receiver 코드에 노출하지 않는다.
