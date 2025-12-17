# Module

## 목적
소스코드를 논리적 단위로 구조화하고 export를 명시적으로 관리한다.

## 규칙
- Module은 정해진 디렉토리 구조를 따른다.
- `internal/`에 소스코드를 작성한다.
- `__init__.py`에서 명시적으로 export한다.
- 중첩 구조는 `<sub-module>/`을 통해 구성한다.

### 디렉토리 구조
```
<module>/
    <sub-module>/
    internal/
    test/
    docs/
    __init__.py
    README.md
```

### 디렉토리 설명
- `<sub-module>/`: 하위 모듈 (중첩 구조)
- `internal/`: 소스코드
- `test/`: 테스트 코드
- `docs/`: 모듈 세부 문서
- `__init__.py`: export 명시
- `README.md`: 모듈 소개

## 적용 범위
프로젝트 전체 코드 구조에 적용된다.
