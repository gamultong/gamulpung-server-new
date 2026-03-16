# BOMB-POSITION

이는 사용자가 지뢰를 설치했을 때, 해당 지점을 시야에 포함하는 사용자에게 발행됩니다.

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
