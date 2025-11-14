# TILES-STATE

이는 사용자의 `window`안 `tile`이 변화 되었을 때 발행됩니다.
`tile`의 정보 표기는 [참조1](/docs/RFC/6.%20Tile%20마스킹.md)을 참고하세요.

## Payload

```json
{   
    "tiles_li": [
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