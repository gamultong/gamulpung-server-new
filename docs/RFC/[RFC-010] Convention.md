# Convention

## 목적
코드·구현·테스트가 같은 일을 같은 방식으로 하도록, 코드베이스에 정착된 관례를 컨벤션으로 명문화한다.

## 규칙
- 컨벤션은 세 영역으로 나누어 가이드로 관리한다.
    - 코드 작성(명명·타입·주석·로깅·예외): [코드 작성 가이드](/docs/Other/Convention%20guide/Code.md)
    - Handler·Receiver 구현 패턴: [HR 구현 가이드](/docs/Other/Convention%20guide/HR.md)
    - 테스트 배치·명명·작성: [테스트 작성 가이드](/docs/Other/Convention%20guide/Test.md)
- 컨벤션은 정착된 관례의 명문화다. 관례가 바뀌면 가이드도 함께 갱신한다.
- 도구로 강제할 수 있는 컨벤션은 도구로 강제한다 (lint, CI 게이트, 명명 검증 테스트).

## 적용 범위
프로젝트 전체 소스 코드와 테스트에 적용된다.
