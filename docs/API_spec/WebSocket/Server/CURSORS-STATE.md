# CURSORS-STATE

이는 사용자 `window`의 `Cursor`정보가 변경될 경우 발행됩니다.
이는 자신의 `cursor`와 타인의 `cursor`를 포함합니다.

## Payload

```json
{   
    "cursors" :[
        <cursor>
    ]
}

// <cursor>
{
    "id":str,
    "position": {
        "x": int,
        "y": int
    },
    "active_at": datetime // iso format으로 보냅니다. 'YYYY-MM-DD HH:MM:SS.mmmmmm'
}
```