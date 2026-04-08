import hashlib
from enum import IntEnum

from .codes import TRAINER_TYPES


TRAINER_DATA_COLS = {
    "id"        : "id",
    "name"      : "name",
    "type"      : "type",
    "effect"    : "effect"
}


class Col(IntEnum):
    Id = 0
    Name = 1
    Type = 2
    Effect = 3


TRAINER_SCHEMA = [
    "id",
    "type",
    # effect
]


def get_trainer_id(name, type, desc):
    """Generates a unique ID for a trainer block."""
    stats_str = f"{name}{type}{desc}"
    h = hashlib.md5(stats_str.encode()).digest()
    return int.from_bytes(h, 'big') & ((1 << 63) - 1)


def trainer_vector(row: tuple) -> list:
    """
    Vectorizes a row from the raw/trainer.parquet file
    :param row: Raw trainer data row
    :return: None or vectorized trainer
    """
    return [
        row[Col.Id],
        _encode_trainer_type(row[Col.Type])
    ]


def _encode_trainer_type(t_type: str) -> int:
    return TRAINER_TYPES.index(t_type)