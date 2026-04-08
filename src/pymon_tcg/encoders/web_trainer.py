from selectolax.parser import HTMLParser
import polars as pl
from .web_tools import scrape_card_print
from .trainer import get_trainer_id, TRAINER_DATA_COLS
from .card import CARD_COLS


TRAINER_FIELDS = [
    'effect'
]


def scrape_trainer_details(tree: HTMLParser):
    """
    Scrapes the HTML for trainer card data

    :param tree: HTML tree

    :returns: dictionary of the trainer and card print data
    """

    name = tree.css(".card-text-title")[0].text(strip=True).lower()
    ttype = tree.css(".card-text-type")[0].text(strip=True).split("-")[-1].strip().lower()
    desc = tree.css(".card-text-section")[1].text().lower().strip()
    illustrator = tree.css(".card-text-artist a")[0].text(strip=True)

    card_print = scrape_card_print(tree)

    return {
        "name": name,
        "card_type": "trainer",
        "type": ttype,
        "effect": desc,
        "illustrator": illustrator,
        "id": get_trainer_id(name, ttype, desc)
    } | card_print


def separate_trainer_data(trainer_df: pl.DataFrame):
    """
    Separates the raw scraped data into the trainer and card data rows

    :param pkmn_df: Scraped trainer dataframe

    :returns: trainer and card data rows
    """

    trainer_data = (
        trainer_df.select(TRAINER_DATA_COLS.keys()).rename(TRAINER_DATA_COLS)
        .unique(subset=["id"], keep="first")
    )

    trainer_cards = trainer_df.select(CARD_COLS.keys()).rename(CARD_COLS)

    return trainer_data, trainer_cards