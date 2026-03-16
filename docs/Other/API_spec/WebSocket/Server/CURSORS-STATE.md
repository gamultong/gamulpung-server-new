# CURSORS-STATE

이는 사용자 `window`의 `Cursor`정보가 변경될 경우 발행됩니다.
이는 자신의 `cursor`와 타인의 `cursor`를 포함합니다.

## Payload

```json
{
    "cursors": [
        <cursor>
    ]
}

// <cursor>
{
    "id": str,
    "position": {
        "x": int,
        "y": int
    },
    "active_at": datetime, // ISO 형식: 'YYYY-MM-DDTHH:MM:SS.mmmmmm'
    "score": int,
    "items": {
        "bomb": int
    },
    "color": int
}
```

`color` 값 규칙
- `1=RED`
- `2=BLUE`
- `3=YELLOW`
- `4=PURPLE`

주의
- `width`, `height`는 내부 상태이며 `CURSORS-STATE` payload에 포함되지 않습니다.
