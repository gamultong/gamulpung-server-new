# CREATE-CURSOR

이는 사용자의 `Cursor`를 생성할 때 사용됩니다.

## Payload

```json
{
    "width": int,
    "height": int,
    "color": int
}
```

**Note:**
- `width`, `height`: 클라이언트의 viewport 크기 (필수)
- `color`: cursor 색상 번호 (`1=RED`, `2=BLUE`, `3=YELLOW`, `4=PURPLE`) (필수)
- 이미 사용 중인 `color`는 사용할 수 없습니다.
- `color`는 생성 시에만 설정되며 변경할 수 없습니다.
- 커서는 항상 (0, 0) 위치에 생성됩니다

## SCENARIO
1. `CREATE-CURSOR` 발행
2. `CURSORS-STATE` 발행
    -> 생성된 cursor를 포함한 시야 범위 내 모든 커서 정보 전달
