# TILES-STATE

이는 사용자의 `window`안 `tile`이 변화 되었을 때 발행됩니다.

## Payload

```json
{   
    "tiles_li": [
        <elem>
    ]
}
s
// <elem>
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