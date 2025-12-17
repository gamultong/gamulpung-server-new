# OPEN-TILES
이는 사용자가 `Tile`을 열 때 사용됩니다.

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
1. `OPEN-TILES` 발행
2. `TILES-STATE` 발행
    -> tiles 정보 변경
case 지뢰가 있다면:
3. `EXPLSION` 발행
4. `CURSORS-STATE` 발행
    -> 지뢰로 인한 커서 정보 변경