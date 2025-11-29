Section 생성 방식에 대한 의사결정

## Context

Gamulpung은 무한한 크기의 맵을 제공하는 온라인 지뢰찾기 게임입니다. 사용자가 새로운 영역과 상호작용할 때마다 Section을 생성하고 지뢰 수를 계산(numbering)해야 합니다.

초기 구현에서는 사용자 요청 시점에 즉시 Section을 생성하고 numbering하는 방식을 사용했습니다:
```
요청 → 생성 → numbering → 응답
```

이 방식은 다음과 같은 문제가 있었습니다:
- 사용자 요청마다 Section 생성과 numbering이 동기적으로 수행되어 응답 지연 발생
- 맵 확장 시 여러 Section을 순차적으로 생성해야 하는 경우 지연 누적

## Decision

**완충지대(buffer zone) 전략**을 채택하여 Section을 3단계 상태로 관리합니다:

1. **closed section**: 단순 생성된 Section (numbering 전)
2. **numbering section**: numbering이 완료된 Section
3. **interaction section**: 사용자와 상호작용 가능한 Section

### 생성 플로우

사용자가 numbering section과 상호작용하면:
1. 해당 Section을 interaction section으로 격상
2. 주변 1칸의 closed section을 numbering section으로 격상 (없으면 closed section 생성 후 격상)

```
(미리 생성됨) → 요청 → 다음 생성 예약 → 응답
```

## Alternatives Considered

### 1. 즉시 생성 방식 (기존)
- 장점: 단순한 구현, 메모리 효율적
- 단점: 응답 지연, 사용자 경험 저하

### 2. 사전 생성 방식
모든 Section을 미리 생성하고 numbering
- 장점: 가장 빠른 응답
- 단점: 무한 맵에서 불가능, 메모리 낭비

### 3. 완충지대 방식 (채택)
상호작용 가능한 Section 주변에 미리 numbering된 Section 유지
- 장점: 빠른 응답, 확장 가능
- 단점: 메모리 사용 증가 (주변 1칸)

## Consequences

### 긍정적 영향
- ✅ 사용자 요청에 대한 빠른 응답 (numbering 시간 제거)
- ✅ 무한 맵 확장 가능 (필요한 영역만 생성)
- ✅ 자연스러운 맵 탐험 경험

### 부정적 영향
- ⚠️ 메모리 사용 증가 (interaction section 주변 1칸의 numbering section 유지)
- ⚠️ Section 상태 관리 복잡도 증가 (3가지 상태)

### 완화 방안
- Section은 주변 Section의 상태 flag를 유지하여 효율적 관리
- 오랫동안 사용되지 않는 Section은 가비지 컬렉션 (향후 구현 가능)

## 참고
- [GitHub Issue #13](https://github.com/gamultong/gamulpung-server-new/issues/13)
