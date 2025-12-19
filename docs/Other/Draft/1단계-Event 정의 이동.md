# 1단계: Event 정의 이동

## 목표

Event 발행 규칙을 Data Layer로 이동.

---

## 작업

DataObj별 Event 발행자 구현:
- Cursor
- Tile
- Tiles

각 발행자: `get_events(old, new) -> list[Event]`

---

## 결과

Event 발행 규칙이 Data Layer에서 중앙 관리됨.
