from pathlib import Path
import polars as pl

from .ability import ability_vector, ABILITY_SCHEMA
from .attack import attack_vector, ATTACK_SCHEMA
from .trainer import trainer_vector, TRAINER_SCHEMA
from .pymon import pokemon_vector, PYMON_SCHEMA, Col as PymonCol


def vectorize_trainers_df(source: str = "./data/raw", to: str = "./data/encoded") -> None:
    """
    Generates and saves the vectorized version of the trainers dataframe
    :param source: Location of the raw data file
    :param to: Location to save the vectorized data
    :return: None
    """
    
    p_to = Path(to)
    p_to.mkdir(parents=True, exist_ok=True)
    raw = pl.read_parquet(Path(source) / "trainers.parquet")
    vectors = [trainer_vector(r) for r in raw.iter_rows()]
    pl.DataFrame(
        vectors,
        schema=TRAINER_SCHEMA, 
        orient="row"
    ).write_parquet(p_to / "trainers.vectors.parquet")


def vectorize_abilities_df(source: str = "./data/raw", to: str = "./data/encoded") -> None:
    """
    Generates and saves the vectorized version of the abilities dataframe
    
    :param source: Location of the raw data file
    :param to: Location to save the vectorized data
    
    :return: None
    """

    p_to = Path(to)
    p_to.mkdir(parents=True, exist_ok=True)
    raw = pl.read_parquet(Path(source) / "abilities.parquet")
    vectors = [ability_vector(r) for r in raw.iter_rows()]
    pl.DataFrame(
        vectors, 
        schema=ABILITY_SCHEMA,
        orient="row"
    ).write_parquet(p_to / "abilities.vectors.parquet")


def vectorize_attacks_df(source: str = "./data/raw", to: str = "./data/encoded") -> None:
    """
    Generates and saves the vectorized version of the attacks dataframe
    
    :param source: Location of the raw data file
    :param to: Location to save the vectorized data
    
    :return: None
    """

    p_to = Path(to)
    p_to.mkdir(parents=True, exist_ok=True)
    raw = pl.read_parquet(Path(source) / "attacks.parquet")
    vectors = [attack_vector(r) for r in raw.iter_rows()]
    pl.DataFrame(
        vectors, 
        schema=ATTACK_SCHEMA,
        orient="row"
    ).write_parquet(p_to / "attacks.vectors.parquet")


def vectorize_pymon_df(source: str = "./data/raw", to: str = "./data/encoded") -> None:
    """
    Generates and saves the vectorized version of the pymon dataframe
    
    :param source: Location of the raw data file
    :param to: Location to save the vectorized data
    
    :return: None
    
    :raises FileNotFoundError: Requires vectorized abilities and attacks in the 'to' folder
    """

    # Path validation
    p_to = Path(to)
    p_raw = Path(source)
    p_atk = p_to / "attacks.vectors.parquet"
    p_ab = p_to / "abilities.vectors.parquet"
    p_src = p_raw / "pymon.parquet"

    if not p_atk.exists() or not p_ab.exists():
        raise FileNotFoundError(f"Pre-encoded vectors missing in {to}")

    # pull parquets
    raw = pl.read_parquet(p_src)
    ab_data = pl.read_parquet(p_ab)
    atk_data = pl.read_parquet(p_atk)

    # join tables for processing
    combined = (
        raw
        .join(ab_data, left_on="ability_id", right_on="id", how="left", suffix="_ab")
        .join(atk_data, left_on="attack1_id", right_on="id", how="left", suffix="_atk1")
        .join(atk_data, left_on="attack2_id", right_on="id", how="left", suffix="_atk2")
    )

    # get column counts for vectors
    c_pk = len(raw.columns)
    c_ab = len(ab_data.columns) - 1
    c_at = len(atk_data.columns) - 1

    # generate vectors
    vectors = []
    for row in combined.iter_rows():
        pk_t = row[:c_pk]

        s_ab = c_pk
        ab_t = [row[PymonCol.AbId]] + list(row[s_ab : s_ab + c_ab])
        
        s_at1 = s_ab + c_ab
        at1_t = [row[PymonCol.Atk1Id]] + list(row[s_at1 : s_at1 + c_at])
        
        s_at2 = s_at1 + c_at
        at2_t = [row[PymonCol.Atk2Id]] + list(row[s_at2 : s_at2 + c_at])

        vectors.append(
            pokemon_vector(
                pk_t,
                ab_t if ab_t[0] is not None else [0] * (c_ab + 1),
                at1_t if at1_t[0] is not None else [0] * (c_at + 1),
                at2_t if at2_t[0] is not None else [0] * (c_at + 1)
            )
        )

    # create dataframe
    pl.DataFrame(vectors, schema=PYMON_SCHEMA, orient="row", infer_schema_length=None).write_parquet(p_to / "pymon.vectors.parquet")



def vectorize_raw_data(source: str = "./data/raw", to: str = "./data/encoded") -> None:
    """
    Generates and saves the vectorized version of the raw data
    :param source: Location of the raw data files
    :param to: Location to save the vectorized data
    :return: None
    """

    print("Vectorizing data sets")

    message_start("pokemon", source, to)
    vectorize_trainers_df(source=source, to=to)
    message_end()
    
    message_start("abilities", source, to)
    vectorize_abilities_df(source=source, to=to)
    message_end()
    
    message_start("attacks", source, to)
    vectorize_attacks_df(source=source, to=to)
    message_end()

    message_start("pymon", source, to)
    vectorize_pymon_df(source=source, to=to)
    message_end()

def message_start(name: str, source: str, to: str) -> None:
    if source[:2] == "./": source = source[2:]
    if to[:2] == "./": to = to[2:]
    print(f" - Converting '{source}/{name}.parquet' => '{to}/{name}.vectors.parquet'", end='')

def message_end() -> None:
    print(" COMPLETED")