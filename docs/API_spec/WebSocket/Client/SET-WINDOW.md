# SET-WINDOW
이는 사용자가 `window`를 설정할 때 사용됩니다.

## Payload

```json
{
    "width": int,
    "height": int
}
```

## SINARIO
1. `SET-WINDOW` 발행
2. `TILES-STATE` 발행
    -> 시아 범위 변경에 따른 정보 전달
3. `CURSORS-STATE` 발행
    -> 시아 범위 변경에 따른 정보 전달