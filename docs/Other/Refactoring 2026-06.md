# 2026-06 구조·스타일 감사 반영 리팩터링

전체 구조/패턴 감사 결과를 주제별 브랜치로 반영했다. 각 변경의 상세는 해당 브랜치의 커밋 메시지 참고.

## 반영 내역
- `chore/tooling`: 의존성을 직접 import 기준으로 정리(전이 의존성 freeze 덤프 제거), dev 그룹 분리, ruff 도입, 미사용 import 85건 정리
- `fix/serialization`: `DataObj.from_dict`가 문자열 어노테이션·상속·제네릭을 해석하도록 수정(중첩 필드 무음 파손), `Tiles.to_dict` return 누락·원본 변형 수정, 회귀 테스트 추가
- `fix/exception-logging`: 문자열 raise 2건·bare except 제거, 미지 이벤트에 `InvalidEvent_Exception` 사용, receiver 8곳 커서 미존재 가드(세션 끊김 방지), loguru `%s` 인자 유실 3건 수정
- `fix/module-boundaries`: 타 모듈 `internal` 직접 import 제거(공개 export 경유), `_get_db`→`get_db`, `fetch_section` stale 반환 수정, `make_section` 지뢰 밀도 가드 수식·조건 수정
- `refactor/test-utils`: unittest 잔재(TCM·set_board 등) 제거, `create_cursor_at_position` 6벌 복붙 승격, conftest 31줄 복제 제거, 테스트의 git 추적 파일 변경 문제 수정
- `fix/naming`: `togle_flag`→`toggle_flag`, `SETTED_WINDOW`→`WINDOW_SET`, `law`→`raw` 등 공개 API 오타 수정
- `chore/dead-code`: utils/·레거시 러너·루트 prometheus.yml·MetricsConfig 삭제, 62MB 바이너리 git 추적 제거, receiver 등록을 server.py로 일원화, CI lint 게이트 추가
- `docs/sync`: Lifecycle/Emitter를 [[RFC-008]](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md)·[[RFC-009]](/docs/RFC/%5BRFC-009%5D%20Emitter.md)로 공식화, 이벤트 scope·cursor board Glossary 추가, 깨진 링크 8건 수정

## 남은 작업 (의사결정 필요)
- 타일 마스킹: `BoardHandler.fetch` 경로가 닫힌 타일의 mine 비트를 그대로 클라이언트에 전송한다. `Tiles.hide_info`를 와이어 경로에 적용할지는 프로토콜 변경이라 보류 (클라이언트 영향 검토 필요)
- naive datetime: 커서 생존/부활 판정이 타임존 없는 벽시계에 의존하고 `active_at`이 API 스펙에 고착됨
- repository 중복: map/cursor 저장소 약 100줄 평행 복제, 스코어보드 갱신 블록 3중 복붙, `RankRange(1, 10)` 등 매직 넘버 상수화
- ClientMessage 입력 검증: 8종 중 CreateCursor만 수동 검증, 나머지는 무검증 통과
- EventBroker: 전역 정적 상태(테스트 격리 불가), receiver 예외의 Handler 역전파, receiver의 직접 publish(단방향 규칙 위반)
- CI/CD: CD가 테스트에 게이트되지 않음, Dockerfile `COPY . .` 캐시·이미지 비대, 타입체크(mypy/pyright) 미도입
- builtin 가리기(`id` 18곳 등), 테스트 고정 `sleep(0.1)` 9곳의 폴링 전환
