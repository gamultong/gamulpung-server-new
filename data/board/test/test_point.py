from data.board import Point, PointRange


class TestPointRangeFromDict:
    def test_중첩_Point가_객체로_복원된다(self):
        """future annotations로 인해 raw dict가 그대로 들어가던 회귀 검증"""
        pr = PointRange.from_dict({
            "top_left": {"x": 0, "y": 3},
            "bottom_right": {"x": 3, "y": 0},
        })

        assert isinstance(pr.top_left, Point)
        assert isinstance(pr.bottom_right, Point)
        assert pr.top == 3
        assert pr.width == 4

    def test_to_dict_from_dict_왕복이_동등하다(self):
        pr = PointRange(Point(0, 3), Point(3, 0))

        assert PointRange.from_dict(pr.to_dict()) == pr
