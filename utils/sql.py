from functools import cache
from pathlib import Path


@cache
def get_sql(sql_dir: str | Path, filename: str):
    with open(Path(sql_dir) / filename, "r", encoding="utf-8") as f:
        query = f.read()
    return query
