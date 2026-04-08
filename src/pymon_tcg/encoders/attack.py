from enum import IntEnum
from .tools import get_hash

from .codes import ENERGY_TYPES, ENERGY_TYPES_SHORT


ATTACK_COLS = {
    "id"            : "id", 
    "cost"          : "cost", 
    "name"          : "name", 
    "damage"        : "damage", 
    "description"   : "effect"
}


class Col(IntEnum):
    Id = 0
    Cost = 1
    Name = 2
    Damage = 3
    Effect = 4


ATTACK_SCHEMA = [
    "id", 
    *[ENERGY_TYPES[i][:3] for i in range(len(ENERGY_TYPES_SHORT))], 
    "dmg",
    # TODO effect
]


def get_attack_id(cost, name, damage, desc):
    """Generates a unique ID for an attack block."""
    return get_hash(cost, name, damage, desc)


def attack_vector(row: tuple | None) -> list | None:
    """
    Vectorizes a row from the raw/attack.parquet file
    
    :param row: Raw attack data row
    
    :return: None or vectorized attack
    """

    if row is None: return [0] * len(ATTACK_SCHEMA)
    return [
        row[Col.Id],
        *_encode_atk_cost(row[Col.Cost]),
        row[Col.Damage],
    ]


def _encode_atk_cost(cost: str) -> list:
    """
    One-hot encodes an attack cost
    
    :param cost: Cost string (ex. 'ccd')
    
    :return: ordered list of energy counts in cost
    """

    energies = [0] * len(ENERGY_TYPES_SHORT)
    
    if cost == '0':
        return energies

    for char in cost:
        idx = ENERGY_TYPES_SHORT.index(char)
        energies[idx] += 1
    
    return energies