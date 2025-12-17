# Section 생성 전략 채택

## 상황
무한 맵에서 사용자 요청 시 즉시 Section 생성 및 numbering을 수행하면 응답 지연이 발생하여 사용자 경험이 저하되었다. ([GitHub Issue #13](https://github.com/gamultong/gamulpung-server-new/issues/13))

## 결정
완충지대(buffer zone) 전략을 채택하여 상호작용 가능한 Section 주변에 미리 numbering된 Section을 유지한다. ([[RFC-005] Section 생성 및 numbering](/docs/RFC/%5BRFC-005%5D%20Section%20%EC%83%9D%EC%84%B1%20%EB%B0%8F%20numbering.md))

## 근거(요약)
- 즉시 생성 방식은 응답 지연을 유발한다.
- 완전 사전 생성은 무한 맵에서 불가능하다.
- 완충지대 방식은 빠른 응답과 무한 확장을 모두 만족한다.
