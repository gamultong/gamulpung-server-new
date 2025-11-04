from core.dataobj import DataObj


class Cursor(DataObj):
    id: str
    width: int
    height: int

    def to_dict(self):
        dict = super().to_dict()
        del dict["width"]
        del dict["height"]

        return dict
