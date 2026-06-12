# event

Event 구조와 scope 메커니즘을 정의하는 모듈.

- Event는 이벤트명과 payload를 담는 제네릭 컨테이너다.
- EventEnum은 대문자+하이픈 명명을 메커니즘으로 강제하고, scope를 계층 누적한다. ([event](/docs/Glossary/dev/event.md))
- 어떤 scope가 존재하는가(정책)는 data/event가 정의한다. 이 모듈은 메커니즘만 제공한다.
