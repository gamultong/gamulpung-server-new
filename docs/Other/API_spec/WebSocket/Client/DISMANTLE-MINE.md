# DISMANTLE-MINE

이는 사용자가 지뢰를 해체할 때 사용됩니다.
## Payload

```json
{
    "position": {
        "x": int,
        "y": int
    }
}
```

## SCENARIO
1. `DISMANTLE-MINE` 발행
2. `TILES-STATE` 발행
    -> tiles 정보 변경
3. `CURSORS-STATE` 발행
    -> 해체 성공 or 실패로 인한 커서 정보 변경
