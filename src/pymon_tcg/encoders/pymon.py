from enum import IntEnum
from .tools import get_hash

from .ability import ABILITY_SCHEMA
from .attack import ATTACK_SCHEMA
from .codes import STAGES, ENERGY_TYPES


PKMN_DATA_COLS = {
    "id"        : "id",
    "name"      : "name",
    "type"      : "type",
    "hp"        : "hp",
    "stage"     : "stage",
    "ab_id"     : "ability_id",
    "a1_id"     : "attack1_id",
    "a2_id"     : "attack2_id",
    "weakness"  : "weakness",
    "retreat"   : "retreat",
}


class Col(IntEnum):
    Id = 0
    Name = 1
    Type = 2
    Hp = 3
    Stage = 4
    AbId = 5
    Atk1Id = 6
    Atk2Id = 7
    Weakness = 8
    Retreat = 9


PYMON_SCHEMA = [
    'id',           'type', 
    'hp',           'stage', 
    'ab_id',        'atk1_id',  'atk2_id',
    'ab_flag',      *[f"ab_{str(n).lower()}" for n in ABILITY_SCHEMA[1:]],  # skip ids
    'atk1_flag',    *[f"a1_{str(n).lower()}" for n in ATTACK_SCHEMA[1:]],
    'atk2_flag',    *[f"a2_{str(n).lower()}" for n in ATTACK_SCHEMA[1:]],
    'weakness',     'retreat'
]


def get_pokemon_id(name, type, hp, stage, a1id, a2id, weakness, retreat):
    """Generates a unique ID for a pokemon block."""
    return get_hash(name, type, hp, stage, a1id, a2id, weakness, retreat)


def pokemon_vector(
    row: tuple,
    ability: list,
    a1: list,
    a2: list
) -> list:
    return [
        row[Col.Id], 
        _encode_type(row[Col.Type]), 
        row[Col.Hp], 
        _encode_stage(row[Col.Stage]),
        row[Col.AbId],
        row[Col.Atk1Id],
        row[Col.Atk2Id],
        int(ability[0] != 0), *ability[1:],
        int(not a1[0] in [None, 0]), *a1[1:],
        int(not a2[0] in [None, 0]), *a2[1:],
        _encode_type(row[Col.Weakness]), 
        row[Col.Retreat]
    ]


def _encode_type(e_type: str) -> int:
    if e_type == "none": return -1
    try:
        return ENERGY_TYPES.index(e_type)
    except ValueError:
        raise Exception(f"e_type '{e_type}' is not handled")


def _encode_stage(stage: str) -> int:
    return STAGES[stage]