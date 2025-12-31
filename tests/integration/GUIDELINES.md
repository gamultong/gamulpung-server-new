# 통합 테스트 가이드

## 테스트 실패 원인 분석

### 문제 상황

커서 생성 후 `CURSORS_STATE`만 기다리고 이벤트 목록을 비웠는데, 커서 생성의 다른 부수 효과들(예: `TILES_STATE`)이 비동기로 계속 도착하는 중이었음.

그래서 깃발 설치 요청 후 받은 `TILES_STATE`가 실제로는:
- "커서 생성으로 인한 타일 상태 변경"일 수 있고
- 진짜 "깃발 설치로 인한 타일 상태 변경"은 아직 안 왔거나 이미 지나갔을 수 있음

이벤트 종류만 확인하고 서버 상태를 직접 조회했더니, 깃발이 실제로 꽂히기 전에 조회해서 실패.

### 근본 원인

1. `clear()` 전에 모든 부수 효과 이벤트를 기다리지 않음
2. 이벤트 타입만 확인하고 내용은 검증하지 않음
3. 서버 내부 상태를 직접 조회하여 타이밍 이슈 발생

## 통합 테스트 작성 규칙

### 1. 이벤트 검증 시 내용까지 정확히 확인

메시지의 payload까지 검증해서 "내가 지금 기대하는 바로 그 변경사항"인지 확인해야 함.

```python
# ❌ 잘못된 예: 이벤트 타입만 확인
assert_wait_event(cl_a.conn.send, ServerEvent.TILES_STATE)
tile = await BoardHandler.fetch_tile(Point(1, 1))
assert tile.is_flag == True

# ✅ 올바른 예: 메시지 내용까지 검증
flagged_tile = Tile.create(is_open=False, is_mine=False, is_flag=True, number=0)
tiles = Tiles(data=bytearray([flagged_tile.data]), width=1, height=1)

expected_message = Message(
    event=Event(
        event_name=ServerEvent.TILES_STATE,
        payload=ServerMessage.TilesState(
            tiles_li=[
                ServerMessage.TilesState.Elem(
                    data=tiles.to_str(),
                    range=PointRange(Point(1, 1), Point(1, 1))
                )
            ]
        )
    )
)
assert_wait_message(cl_a.conn.send, expected_message)
```

### 2. 이벤트 타입만 확인하는 것은 단순 대기용

어떤 처리가 완료될 때까지 기다리는 용도로만 `assert_wait_event` 사용.

```python
# ✅ 올바른 사용: 커서 생성 완료 대기
cl_a.ws.send_json({
    "header": {"event": ClientEvent.CREATE_CURSOR.value},
    "payload": {"width": 1, "height": 1}
})
assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)
```

### 3. 상태 변경 전에는 반드시 모든 부수 효과를 기다려야 함

이전 작업의 모든 부수 효과 이벤트가 완전히 소진될 때까지 기다리거나, 메시지 내용을 정확히 검증해서 다른 이벤트와 구별.

```python
# ❌ 잘못된 예: clear() 전에 부수 효과를 충분히 기다리지 않음
assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)
cl_a.conn.send.await_args_list.clear()  # TILES_STATE 등 다른 이벤트가 아직 오는 중일 수 있음

# ✅ 올바른 예: 메시지 내용을 검증하여 정확한 이벤트 구별
# clear() 없이 바로 다음 작업의 결과를 payload까지 검증
```

## 권장 패턴

### Tile 데이터 변환

```python
# Tile -> 문자열 변환
tile = Tile.create(is_open=False, is_mine=False, is_flag=True, number=0)
tiles = Tiles(data=bytearray([tile.data]), width=1, height=1)
data_str = tiles.to_str()  # hex 문자열로 변환
```

### 메시지 검증

```python
expected_message = Message(
    event=Event(
        event_name=ServerEvent.TILES_STATE,
        payload=ServerMessage.TilesState(
            tiles_li=[
                ServerMessage.TilesState.Elem(
                    data=tiles.to_str(),
                    range=PointRange(Point(x, y), Point(x, y))
                )
            ]
        )
    )
)
assert_wait_message(cl_a.conn.send, expected_message)
```

## 요약

- **검증**: 이벤트 타입만 확인하지 말고 payload까지 검증
- **대기**: `assert_wait_event`는 단순 대기 용도로만 사용
- **동기화**: `clear()` 전에 모든 부수 효과를 소진하거나 메시지 내용으로 구별
