from enum import IntEnum
from .tools import get_hash

ABILITY_COLS = {
    "ab_id"             : "id", 
    "ab_name"           : "name", 
    "ab_description"    : "effect"
}


class Col(IntEnum):
    Id = 0
    Name = 1
    Effect = 2


ABILITY_SCHEMA = [
    "id",
    # TODO effect
]


def get_ability_id(name, desc):
    """Generates a unique ID for an ability block."""
    return get_hash(name, desc)


def ability_vector(row: tuple | None) -> list | None:
    """
    Vectorizes a row from the raw/ability.parquet file
    
    :param row: Raw ability data row
    
    :return: None or vectorized ability
    """

    if row is None: return [0] * len(ABILITY_SCHEMA)
    return [row[Col.Id]]