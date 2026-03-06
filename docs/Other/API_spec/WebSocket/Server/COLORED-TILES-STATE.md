# COLORED-TILES-STATE

이는 사용자의 `window`안 `cursor_board`가 변화 되었을 때 발행됩니다.
타일 단위 색상 맵 정보는 이 이벤트를 통해 전달됩니다.

## Payload

```json
{   
    "colored_tiles_li": [
        <elem>
    ]
}
```

\<elem> 
```json
{
    "data": string,
    "range": {
        "top_left":{
            "x": int,
            "y": int
        },
        "bottom_right":{
            "x": int,
            "y": int
        }
    }
}
```

**Note:**
- `data`는 타일 순서대로 color 값을 직렬화한 hex 문자열입니다.
- 값 규칙: `0=None`, `1=RED`, `2=BLUE`, `3=YELLOW`, `4=PURPLE`
