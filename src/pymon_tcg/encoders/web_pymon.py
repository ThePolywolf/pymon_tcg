from selectolax.parser import HTMLParser
import polars as pl
from .web_tools import scrape_card_print
from .ability import get_ability_id, ABILITY_COLS
from .attack import get_attack_id, ATTACK_COLS
from .pymon import get_pokemon_id, PKMN_DATA_COLS
from .card import CARD_COLS


POKEMON_FIELDS = [
    'hp', 'stage', 'preevo', 'weakness', 'retreat', 'description', 
    'ab_id', 'ab_name', 'ab_description',
    'a1_id', 'a1_cost', 'a1_name' , 'a1_damage', 'a1_description', 
    'a2_id', 'a2_cost', 'a2_name' , 'a2_damage', 'a2_description',
]


def scrape_pkmn_details(tree: HTMLParser) -> dict:
    """
    Scrapes the HTML for pymon card data

    :param tree: HTML tree

    :returns: dictionary of the pymon data
    """

    sections = tree.css(".card-text .card-text-section")

    header = sections[0]
    pkmn_name = header.css(".card-text-name")[0].text(strip=True).lower()
    type_and_hp = header.css(".card-text-title")[0].text(strip=True)[len(pkmn_name):].lower().strip()
    pkmn_type, hp = [t.strip() for t in type_and_hp.split("-")[1:]]
    hp = int(hp.split(" ")[0])
    card_text_types = [t.strip() for t in header.css(".card-text-type")[0].text(strip=True).lower().split("-")]
    stage = card_text_types[1]
    pre_evo = card_text_types[2][len("evolves from"):] if stage != "basic" else None
    weakness, retreat = tree.css(".card-text-section .card-text-wrr")[0].text(strip=True).lower()[len('weakness: '):].split("retreat: ")
    illustrator = tree.css(".card-text-artist a")[0].text(strip=True)
    try:
        # normal description
        description = tree.css(".card-text-flavor")[0].text(strip=True)
    except Exception as e:
        # ex/mega-ex rules
        description = tree.css(".card-text-section")[-2].text().strip()

    card_print = scrape_card_print(tree)
    
    card_data = {
        "name": pkmn_name,
        "card_type": "pokemon",
        "type": pkmn_type,
        "hp": hp,
        "stage": stage,
        "preevo": pre_evo,
        'ab_id': None,
        'ab_name': None,
        'ab_description': None,
        'a1_id': None,
        'a1_cost': None,
        'a1_name': None,
        'a1_damage': None,
        'a1_description': None,
        'a2_id': None,
        'a2_cost': None,
        'a2_name': None,
        'a2_damage': None,
        'a2_description': None,
        'weakness': weakness,
        'retreat': int(retreat),
        'illustrator': illustrator,
        'description': description,
    }

    abilities = tree.css(".card-text-ability")
    if len(abilities) > 1:
        raise Exception("More than one ability is not handled")

    if len(abilities) == 1:
        ab = abilities[0]
        
        ab_name = ab.css(".card-text-ability-info")[0].text(strip=True)[len("ability: "):].lower().strip()
        ab_desc = ab.css(".card-text-ability-effect")[0].text().lower().strip()
        ab_id = get_ability_id(ab_name, ab_desc)
        
        card_data["ab_name"] = ab_name
        card_data["ab_description"] = ab_desc
        card_data["ab_id"] = ab_id

    atk_count = 0
    for atk in tree.css('.card-text-attack'):
        atk_count += 1
        atk_cost = atk.css(".card-text-attack-info .ptcg-symbol")[0].text(strip=True).lower()
        atk_info_splits = atk.css(".card-text-attack-info")[0].text(strip=True)[len(atk_cost):].lower().strip().split(" ")
        try:
            _catcher = int(atk_info_splits[-1][-2])

            atk_name = " ".join(atk_info_splits[:-1])
            
            try:
                atk_dmg = int(atk_info_splits[-1])
            except Exception as e:
                atk_dmg = int(atk_info_splits[-1][:-1])
        except Exception as e:
            atk_name = " ".join(atk_info_splits)
            atk_dmg = 0

        try:
            atk_desc = atk.css(".card-text-attack-effect")[0].text(strip=True).lower()
        except Exception as e:
            atk_desc = None

        card_data[f"a{atk_count}_id"] = get_attack_id(atk_cost, atk_name, atk_dmg, atk_desc)
        card_data[f"a{atk_count}_cost"] = atk_cost
        card_data[f"a{atk_count}_name"] = atk_name
        card_data[f"a{atk_count}_damage"] = atk_dmg
        card_data[f"a{atk_count}_description"] = atk_desc
    
    if atk_count > 2:
        print(f"WARNING: More than two attacks isn't handled ({pkmn_name})")

    card_data['id'] = get_pokemon_id(card_data["name"], card_data["type"], card_data["hp"], card_data["stage"], card_data["a1_id"], card_data["a2_id"], card_data["weakness"], card_data["retreat"])

    return card_data | card_print


def separate_pokemon_data(pkmn_df: pl.DataFrame):
    """
    Separates the raw scraped data into the attack, ability, pokemon, and card datas

    :param pkmn_df: Scraped pymon dataframe

    :returns: pymon, card, ability, and attack data rows
    """
    # assumes no hash collisions

    pkmn_data = (
        pkmn_df.select(PKMN_DATA_COLS.keys()).rename(PKMN_DATA_COLS)
        .unique(subset=["id"], keep="first")
    )

    pkmn_cards = pkmn_df.select(CARD_COLS.keys()).rename(CARD_COLS)

    ability_data = (
        pkmn_df.select(ABILITY_COLS.keys()).rename(ABILITY_COLS)
        .unique(subset=["id"], keep="first")
        .drop_nulls()
    )

    attack_data = (
        pkmn_df.with_columns([
            pl.struct([f"a1_{field}" for field in ATTACK_COLS]).alias("a1").struct.rename_fields(list(ATTACK_COLS.values())),
            pl.struct([f"a2_{field}" for field in ATTACK_COLS]).alias("a2").struct.rename_fields(list(ATTACK_COLS.values())),
            pl.arange(0, pl.len()).alias("idx"),
        ])
        .select(["idx", "a1", "a2"])
        .unpivot(index="idx", on=["a1", "a2"], variable_name="slot", value_name="data")
        .unnest("data")
        .filter(pl.col("id").is_not_null())
        .drop(["idx", "slot"])
        .unique(subset=["id"], keep="first")
    )

    return pkmn_data, pkmn_cards, ability_data, attack_data