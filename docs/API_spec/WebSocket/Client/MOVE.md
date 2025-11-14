# MOVE
이는 사용자의 `Cursor`가 움직일 때 사용됩니다.

## Payload

```json
{
    "position": {
        "x": int,
        "y": int
    }
}
```

## SINARIO
1. `MOVE` 발행
2. `cursors-state` 발행
    -> 내 위치 정보 변경 및 시야 이동의 따른 새로운 `cursor` 정보 
3. `tiles-state` 발행
    - 시야 이동의 따른 새로운 `tile` 정보