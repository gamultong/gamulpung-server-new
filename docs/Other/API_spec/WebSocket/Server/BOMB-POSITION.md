# BOMB-POSITION

이는 아래 경우에 해당 지점을 시야에 포함하는 사용자에게 발행됩니다.
- 사용자가 지뢰를 설치했을 때
- 사용자가 `MOVE`/`SET-WINDOW`로 시야를 갱신했을 때

## Payload
```json
{
    "color": int,
    "position": {
        "x": int,
        "y": int
    }
}
```

**Note:**
- `color`: 지뢰를 설치한 커서의 색깔
- `position`: 설치된 지뢰의 좌표
