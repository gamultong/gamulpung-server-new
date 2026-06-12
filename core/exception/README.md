# exception

도메인 예외의 공통 베이스(BaseExp) 모듈.

- BaseExp는 생성 인자를 컨텍스트 데이터로 보관하고 로깅한다.
- 도메인 예외는 BaseExp를 상속해 정의한다 (예: data/conn의 메시지 형식 예외).
