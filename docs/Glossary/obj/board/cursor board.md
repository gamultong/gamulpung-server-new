## 정의
폭탄 폭발로 색칠된 tile의 소유자(cursor)를 기록하는 board. section과 1:1로 cursor_section을 유지한다.

- 색칠: 폭발 시 `TriggerEvent.DRAW-BOARD` → `CursorBoardHandler.draw_board`
- 조회: `CursorBoardHandler.fetch`가 cursor tile을 반환하고, 색 직렬화는 `CursorHandler.to_colored_tiles_data`가 수행한다.

([[FT-008] 폭탄 설치](/docs/Feature/%5BFT-008%5D%20폭탄%20설치.md))
