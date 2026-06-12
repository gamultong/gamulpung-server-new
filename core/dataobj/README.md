# dataobj

프로젝트 전반에서 사용하는 데이터 객체의 공통 베이스 모듈.

- DataObj를 상속하면 서브클래스 정의 시점에 자동으로 dataclass화된다 (보일러플레이트 제거).
- 직렬화 규약: to_dict / from_dict. from_dict는 타입 힌트를 해석해 중첩 DataObj·list·union 필드를 복원한다.
- copy는 필드 단위 재귀 복사본을 만든다. obj를 외부에 내보낼 때는 copy를 사용해 [data](/docs/Glossary/dev/data.md)의 immutable snapshot 규율을 지킨다.

자세한 사용법: [docs/사용법.md](/core/dataobj/docs/사용법.md)
