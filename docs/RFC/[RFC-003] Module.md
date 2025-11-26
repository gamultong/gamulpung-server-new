프로젝트의 Module 구조 및 규칙을 정의합니다.

<!-- TODO: ADR-004 작성 권장 - Module 구조 채택 이유 (Python import 관리, IDE 지원, export 명시 등의 논의 사항) -->

## 개요
Module은 소스코드 집합입니다.

## 구조
```
<module>/
    <sub-module>/
    internal/
        <source1>
        <source2>
    test/
        <test1>
        <test2>
    docs/
        <docs1>
        <docs2>
    __init__.py
    README.md
```

### 디렉토리 설명
- `<submodule>/` : 하위 모듈입니다. 중첩 구조를 위해 고안되었습니다.
- `internal/` : 소스코드를 작성하는 곳입니다.
- `test/` : module에 대한 test를 작성하는 곳입니다.
- `docs/` : module에 대한 세부정보를 작성하는 곳입니다.
- `__init__.py` : module의 export를 명시하는 곳입니다.
- `README.md` : module의 문서 및 소개입니다.
