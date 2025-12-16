from __future__ import annotations
from enum import StrEnum
from data.board import Tile, Tiles

class MapChar(StrEnum):
    CLOSED = "#"
    OPEN   = "."
    FLAG   = "F"
    MINE   = "X"

def compute_adj_counts(lines: list[str]) -> list[list[int]]:
    H, W = len(lines), len(lines[0])
    counts = [[0] * W for _ in range(H)]

    for r in range(H):
        for c in range(W):
            if lines[r][c] != MapChar.MINE:
                continue

            # 이 지뢰 주변 8칸을 +1
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < H and 0 <= nc < W and lines[nr][nc] != MapChar.MINE:
                        counts[nr][nc] += 1

    return counts

def build_tiles(map_s: str) -> Tiles:
    lines = [ln.rstrip("\n") for ln in map_s.splitlines() if ln.strip()]
    H, W = len(lines), len(lines[0])

    print(lines, H, W)

    assert all(len(ln) == W for ln in lines)

    counts = compute_adj_counts(lines)

    print(counts)

    data = []
    for r in range(H):
        for c in range(W):
            ch = lines[r][c]
            print(ch)

            if ch == MapChar.MINE:  # 지뢰
                data.append(Tile.create(is_flag=False, is_mine=True,  is_open=False, number=0).data)

            elif ch == MapChar.OPEN:  # 열린 타일(열림은 열림으로만)
                data.append(Tile.create(is_flag=False, is_mine=False, is_open=True,  number=0).data)

            elif ch == MapChar.FLAG:  # 깃발(닫힘 취급 + number 필요)
                data.append(Tile.create(is_flag=True,  is_mine=False, is_open=False, number=counts[r][c]).data)

            elif ch == MapChar.CLOSED:  # 닫힘(닫힘 취급 + number 필요)
                data.append(Tile.create(is_flag=False, is_mine=False, is_open=False, number=counts[r][c]).data)

            elif ch.isdigit():
                data.append(Tile.create(is_flag=False, is_mine=False, is_open=False, number=int(ch)).data)

            else:
                raise ValueError(f"unknown char {ch!r} at {(r,c)}")

    tiles = Tiles(bytearray(data), H, W)

    return tiles
