from data.board import Point
from data.board.cursorboard import Color
from data.cursor import Cursor


def create_cursor_at_position(pos: Point):
    """Cursor.create를 특정 위치에 생성하도록 바꾸는 side_effect 헬퍼

    Example:
        with patch("data.cursor.Cursor.create", side_effect=create_cursor_at_position(Point(0, 0))):
            ...
    """
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
