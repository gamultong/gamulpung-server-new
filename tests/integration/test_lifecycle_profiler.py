"""LifecycleProfiler 테스트

시나리오 테스트에서 Lifecycle profiling 적용 검증
"""
import pytest
import asyncio
from unittest.mock import patch

from server import app
from data.event import ServerEvent, ClientEvent
from data.board import Point, Section, SectionFlag
from data.cursor_board import Color
from handler.cursor import CursorHandler
from tests.utils import PytestTCM, assert_wait_event, build_tiles
from config import BoardConfig
from core.lifecycle import LifecycleProfiler


CL_A = "TestClient_A"


async def opened_board_map(db):
    """5x5 열린 타일 보드"""
    map_str = """\
#####
#...#
#...#
#...#
#####
"""
    tiles = build_tiles(map_str)
    sections = [Section(Point(0, 0), tiles.copy(), flag=SectionFlag.INTERACTIONAL)]
    from handler.board.storage import create_section
    for section in sections:
        await create_section(db, section)


def create_cursor_at_position(pos: Point):
    """Cursor를 특정 위치에 생성하는 헬퍼"""
    from data.cursor import Cursor
    origin_create = Cursor.create

    def create_cursor_effect(
        id: str,
        width: int = 0,
        height: int = 0,
        color: Color = Color.RED,
        **_kwargs,
    ):
        return origin_create(
            id,
            width=width,
            height=height,
            position=pos,
            color=color,
        )

    return create_cursor_effect


@patch.object(BoardConfig, "LENGTH", new=5)
@patch("server.initialize_board", new=opened_board_map)
@pytest.mark.asyncio
async def test_lifecycle_profiler_basic():
    """LifecycleProfiler 기본 동작 검증"""
    with LifecycleProfiler() as profiler:
        # Profiler 활성화 확인
        assert LifecycleProfiler.is_enabled()
        assert LifecycleProfiler.get_current() is profiler

        with PytestTCM(app).append_client(CL_A) as tcm:
            cl_a = tcm.get_client(CL_A)

            # Cursor 생성
            with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
                cl_a.ws.send_json({
                    "header": {"event": ClientEvent.CREATE_CURSOR.value},
                    "payload": {"width": 1, "height": 1, "color": Color.RED.value}
                })
                assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

            await asyncio.sleep(0.1)

        # 기록 확인
        records = profiler.records
        assert len(records) > 0, "Lifecycle 기록이 있어야 함"

        # RLife, HLife 기록 존재 확인
        categories = {r.category for r in records}
        assert "RLife" in categories, "RLife 기록이 있어야 함"
        assert "HLife" in categories, "HLife 기록이 있어야 함"

    # Profiler 비활성화 확인
    assert not LifecycleProfiler.is_enabled()


@patch.object(BoardConfig, "LENGTH", new=5)
@patch("server.initialize_board", new=opened_board_map)
@pytest.mark.asyncio
async def test_lifecycle_profiler_move_scenario():
    """이동 시나리오 profiling 검증"""
    with LifecycleProfiler() as profiler:
        with PytestTCM(app).append_client(CL_A) as tcm:
            cl_a = tcm.get_client(CL_A)

            # Cursor 생성
            with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
                cl_a.ws.send_json({
                    "header": {"event": ClientEvent.CREATE_CURSOR.value},
                    "payload": {"width": 1, "height": 1, "color": Color.RED.value}
                })
                assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

            # 이동
            cl_a.ws.send_json({
                "header": {"event": ClientEvent.MOVE.value},
                "payload": {"position": {"x": 2, "y": 1}}
            })
            assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

            await asyncio.sleep(0.1)

        # 결과 출력
        print("\n=== Lifecycle Profile Result ===")
        print(f"Total records: {len(profiler.records)}")
        print()
        print(f"{'TIMESTAMP':>12} | {'PHASE':5} | {'CAT':5} | {'NAME':35} | ARGS")
        print("-" * 90)
        for r in profiler.records:
            phase = "BEGIN" if r.phase == "B" else "END"
            args_str = str(r.args) if r.args else ""
            print(f"{r.timestamp:>12.0f} | {phase:5} | {r.category:5} | {r.name:35} | {args_str}")
        print()

        # JSON 저장
        profiler.save("tests/profile/move_scenario.json")
        print("Saved to: tests/profile/move_scenario.json")

        # Chrome Trace 형식 검증
        trace_events = profiler.to_trace_events()
        assert len(trace_events) > 0

        # 필수 필드 확인
        for event in trace_events:
            assert "name" in event
            assert "cat" in event
            assert "ph" in event  # B 또는 E
            assert "ts" in event  # 타임스탬프
            assert event["ph"] in ("B", "E")

        # Begin/End 쌍 확인
        begins = [e for e in trace_events if e["ph"] == "B"]
        ends = [e for e in trace_events if e["ph"] == "E"]
        assert len(begins) == len(ends), "Begin과 End 수가 같아야 함"


@patch.object(BoardConfig, "LENGTH", new=5)
@patch("server.initialize_board", new=opened_board_map)
@pytest.mark.asyncio
async def test_lifecycle_profiler_json_output():
    """JSON 출력 검증"""
    import json

    with LifecycleProfiler() as profiler:
        with PytestTCM(app).append_client(CL_A) as tcm:
            cl_a = tcm.get_client(CL_A)

            with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(1, 1))):
                cl_a.ws.send_json({
                    "header": {"event": ClientEvent.CREATE_CURSOR.value},
                    "payload": {"width": 1, "height": 1, "color": Color.RED.value}
                })
                assert_wait_event(cl_a.conn.send, ServerEvent.CURSORS_STATE)

            await asyncio.sleep(0.1)

        # JSON 파싱 가능 확인
        json_str = profiler.to_json()
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)


@pytest.mark.asyncio
async def test_lifecycle_profiler_disabled_by_default():
    """Profiler 미사용 시 기록되지 않음 확인"""
    # Profiler 없이 실행
    assert not LifecycleProfiler.is_enabled()
    assert LifecycleProfiler.get_current() is None
