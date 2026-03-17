# INSTALL-BOMB

이는 사용자가 지뢰를 설치할 때 사용됩니다.
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
1. `INSTALL-BOMB` 발행
2. `CURSORS-STATE` 발행
    -> 지뢰 설치로 인한 커서의 지뢰 개수 변경
3. `BOMB-POSITION` 발행
    -> 설치 지점을 시야에 포함하는 사용자에게 설치 사실 전달
4. `EXPLOSION` 발행
    -> 특정 시간 이후에 지뢰의 폭발
<!-- 색 관련은 만들어지지 않음 -->
5. `?` 발행
    -> 타일의 색 변경

**Note:**
- `BOMB-POSITION`은 `MOVE`/`SET-WINDOW`로 시야가 갱신될 때도 추가 발행될 수 있다.
