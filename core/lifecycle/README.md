# lifecycle

Handler·Receiver의 함수 실행을 관리하는 공통 플랫폼. ([[RFC-008] Lifecycle](/docs/RFC/%5BRFC-008%5D%20Lifecycle.md))

- HLife(Handler용)·RLife(Receiver용)를 데코레이터로 적용한다.
- 함수 내부에서 현재 Lifecycle에 접근해 snapshot·Event를 기록한다.
- RLife 컨텍스트 안의 HLife는 Caller에 자동 등록되어 호출 관계가 추적된다.
- metrics sub-module이 실행 기록을 Prometheus 지표로, profiler가 Chrome Trace로 수집한다.

자세한 사용법: [docs/사용법.md](/core/lifecycle/docs/사용법.md)
