# SET-FLAG
이는 사용자가 `Tile`에 깃발을 설정할 때 사용됩니다.

깃발이 있을 때 -> 깃발 해제
깃발이 없을 때 -> 깃발 설정

## Payload

```json
{
    "position": {
        "x": int,
        "y": int
    }
}
```

## SINARiO
1. `SET-FLAG` 발행
2. `TILES-STATE` 발행