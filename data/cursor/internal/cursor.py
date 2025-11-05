from core.dataobj import DataObj
from data.board import Point, PointRange


class Cursor(DataObj):
    id: str
    position: Point
    width: int
    height: int

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

        return dict

    @classmethod
    def create(cls, id: str, position=Point(0, 0), width=0, height=0):
        return cls(
            id=id,
            position=position.copy(),
            width=width,
            height=height
        )
