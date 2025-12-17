# Section 생성 및 numbering

## 목적
완충지대 전략을 통해 Section을 단계적으로 생성하고 numbering한다. (채택 배경: [ADR-002: Section 생성 전략 채택](/docs/ADR/[ADR-002]%20Section%20생성%20전략%20채택.md))

## 규칙
- Section은 3단계 상태를 가진다: closed -> numbering -> interaction
- numbering section 상호작용 시 주변 1칸을 numbering section으로 격상한다.

### 생성 플로우
1. numbering section에 상호작용
2. 해당 Section을 interaction section으로 격상
3. 주변 1칸 closed section을 numbering section으로 격상

![Section 생성 플로우](/docs/RFC/img/5-1.png)

### closed -> numbering 격상
1. 주변 1칸에 section이 없으면 closed section 생성
2. numbering 수행

## 적용 범위
Section 생성 및 관리에 적용된다. (관련: [GitHub Issue #13](https://github.com/gamultong/gamulpung-server-new/issues/13))
