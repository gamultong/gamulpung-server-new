# CURSORS-STATE

이는 사용자 `window`의 `Cursor`정보가 변경될 경우 발행됩니다.

## Payload

```json
{   
    "cursors" :[
        <cursor>
    ]
}

// <cursor>
{
    "id":str
}
```