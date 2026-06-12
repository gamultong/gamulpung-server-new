from __future__ import annotations
from enum import StrEnum
from data.board import Tile, Tiles

class MapChar(StrEnum):
    CLOSED = "#"
    OPEN   = "."
    FLAG   = "F"
    MINE   = "X"

_NEI8 = [  # 8방향
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]


def compute_adj_counts(lines: list[str], H: int, W: int) -> list[list[int]]:
    counts = [[0] * W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            if lines[r][c] != MapChar.MINE:
                continue

            # 이 지뢰 주변 8칸을 +1
            for dr, dc in _NEI8:
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and lines[nr][nc] != MapChar.MINE:
                    counts[nr][nc] += 1

    return counts


def _tile_byte(ch: str, adj: int) -> int:
    match ch:
        case MapChar.MINE: # 지뢰
            return Tile.create(is_flag=False, is_mine=True,  is_open=False, number=0).data
        case MapChar.OPEN: # 열림
            return Tile.create(is_flag=False, is_mine=False, is_open=True,  number=0).data
        case MapChar.FLAG: # 깃발(근처 지뢰 개수만큼 numbering)
            return Tile.create(is_flag=True,  is_mine=False, is_open=False, number=adj).data
        case MapChar.CLOSED: # 닫힘(근처 지뢰 개수만큼 numbering)
            return Tile.create(is_flag=False, is_mine=False, is_open=False, number=adj).data
        case _ if ch.isdigit(): # 수동 넘버링(근처 지뢰 개수 무시)
            return Tile.create(is_flag=False, is_mine=False, is_open=False, number=int(ch)).data
        case _:
            raise ValueError(f"unknown char {ch!r}")


def map_data_create(lines: list[str], counts:list[list[int]], H: int, W: int) -> bytearray:
    data = bytearray()

    for r in range(H):
        for c in range(W):
            ch = lines[r][c]
            data.append(_tile_byte(ch, counts[r][c]))
            
    return data


def build_tiles(map_s: str) -> Tiles:
    lines = [ln.rstrip("\n") for ln in map_s.splitlines() if ln.strip()]
    H, W = len(lines), len(lines[0])

    assert all(len(ln) == W for ln in lines)

    counts = compute_adj_counts(lines, H, W)
    data = map_data_create(lines, counts, H, W)

    # width=열 수(W), height=행 수(H) — 정사각 맵에서는 차이가 없었음
    return Tiles(data, W, H)