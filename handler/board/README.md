# board

지뢰찾기 board obj를 관리하는 Handler 모듈.

- internal/section_handling: section 생성·numbering·격상 플로우. ([[RFC-005] Section 생성 및 numbering](/docs/RFC/%5BRFC-005%5D%20Section%20생성%20및%20numbering.md))
- storage sub-module: SQLite 영속. SQL은 storage 내부 .sql 파일로만 존재한다.
- 좌표 변환은 data/board에 정의되어 있고 Handler는 조합만 한다. ([[RFC-004] Board와 좌표 체계](/docs/RFC/%5BRFC-004%5D%20Board와%20좌표%20체계.md))
- tile 표현과 마스킹 규칙은 [[RFC-006] Tile 마스킹](/docs/RFC/%5BRFC-006%5D%20Tile%20마스킹.md)을 따른다.
