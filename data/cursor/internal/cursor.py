from core.dataobj import DataObj
from data.board import Point, PointRange
from datetime import datetime

INTERACTION_RANGE = 1


class Cursor(DataObj):
    id: str
    position: Point
    width: int
    height: int
    active_at: datetime

    @property
    def window(self):
        return PointRange(
            Point(self.position.x-self.width, self.position.y+self.height),
            Point(self.position.x+self.width, self.position.y-self.height)
        )

    def in_interaction_range(self, point: Point):
        interaction_range = PointRange(
            Point(self.position.x-INTERACTION_RANGE, self.position.y+INTERACTION_RANGE),
            Point(self.position.x+INTERACTION_RANGE, self.position.y-INTERACTION_RANGE)
        )
        return interaction_range.is_in(point)

    def get_window_range(self):
        left = self.position.x-self.width
        right = self.position.x+self.width
        top = self.position.y+self.height
        bottom = self.position.y-self.height

        return PointRange(
            top_left=Point(left, top),
            bottom_right=Point(right, bottom)
        )

    def to_dict(self):
        dict = super().to_dict()
        del dict["width"]
        del dict["height"]

        dict["active_at"] = self.active_at.isoformat()

        return dict

    @classmethod
    def create(cls, id: str, position=Point(0, 0), width=0, height=0, active_at: datetime | None = None):
        if active_at is None:
            active_at = datetime.now()
        return cls(
            id=id,
            position=position.copy(),
            width=width,
            height=height,
            active_at=active_at
        )
