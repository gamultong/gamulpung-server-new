# Spec Driven Development(SDD)

## 목적
본 문서는 프로젝트 전반에서 적용되는 SDD(Spec Driven Development)의 문서 작성 원칙과 구조를 정의한다. ([[ADR-001] SDD 도입 배경](/docs/ADR/%5BADR-001%5D%20SDD%20%EB%8F%84%EC%9E%85%20%EB%B0%B0%EA%B2%BD.md))

SDD는 문서를 최소 단위로 유지하고, 스펙을 명확하게 남기며, 모듈 기반 개발 및 에이전트 협업에서 일관된 기준을 제공하기 위한 전역 규칙이다.

## 규칙

### 문서 종류
공식 스펙 문서는 **RFC / ADR / Glossary / Feature** 네 종류만 사용한다.

#### RFC ([작성 가이드](/docs/Other/SDD%20guide/RFC.md))
- 프로젝트에서 논의된 컨셉의 결과를 작성한다.

#### ADR ([작성 가이드](/docs/Other/SDD%20guide/ADR.md))
- 의사결정에 사유/근거를 정리/요약하는 문서이다.

#### Glossary ([작성 가이드](/docs/Other/SDD%20guide/Glossary.md))
- 일반적인 의미와 다른 용도로 사용하는 용어를 정의하는 문서이다.

#### Feature(FT) ([작성 가이드](/docs/Other/SDD%20guide/Feature%28FT%29.md))
- 도메인 기능을 정리한 문서이다.

### 문서 작성 가이드
- 문서는 A4 기준 1–2 page 내로 작성한다.
- 문서는 하나의 주제만 다룬다.
- 문서는 한국어로 작성하나, 용어에 한하여 원문 작성한다.

## 적용 범위
해당 가이드는 프로젝트 전체 문서 작성 및 스펙 관리 기준으로 적용된다.
