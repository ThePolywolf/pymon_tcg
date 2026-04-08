import httpx
import polars as pl
from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from .web_pymon import scrape_pkmn_details, separate_pokemon_data, POKEMON_FIELDS
from .web_trainer import scrape_trainer_details, separate_trainer_data, TRAINER_FIELDS


SOURCE = "https://pocket.limitlesstcg.com"

client = httpx.Client(http2=True, timeout=30)

BASE_FIELDS = ['name', 'card_type', 'type', 'illustrator', 'set', 'card', 'rarity', 'id']


def fetch_html(url, client=client):
    """Fastest way to get HTML if JS rendering isn't strictly needed for card details."""

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }
    resp = client.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text


def scrape_card_details(card_url_extension):
    """Processes a single card page and returns data for its scrape table"""

    full_url = SOURCE + card_url_extension
    html = fetch_html(full_url)
    tree = HTMLParser(html)

    card_type = tree.css(".card-text-type")[0].text(strip=True).split("-")[0].strip().lower()

    match card_type:
        case "pokémon":
            return scrape_pkmn_details(tree)
        case "trainer":
            return scrape_trainer_details(tree)

    raise Exception(f"Unknown card type '{card_type}'")


def process_set_batch(card_links):
    """A worker function that handles a batch of links on one CPU core."""

    results = []
    for link in card_links:
        try:
            results.append(scrape_card_details(link))
        except Exception as e:
            print(f"Error scraping {link}: {e}")
    return results


def scrape_for_data(save_path: str = "data/raw"):
    """
    Scrapes the server for all pymon cards
    """

    print("Loading all sets...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(SOURCE + "/cards", wait_until="domcontentloaded")
        
        tree = HTMLParser(page.content())
        set_links = [a.attributes.get("href") for a in tree.css("table tbody tr td:first-child a")]
        
        all_card_links = []
        for s_link in set_links:
            page.goto(SOURCE + s_link, wait_until="domcontentloaded")
            set_tree = HTMLParser(page.content())
            all_card_links.extend([a.attributes.get("href") for a in set_tree.css(".card-search-grid a")])
        
        browser.close()

    num_cores = 8
    chunk_size = len(all_card_links) // num_cores
    chunks = [all_card_links[i:i + chunk_size] for i in range(0, len(all_card_links), chunk_size)]

    print(f"Starting Multi-processed scrape of {len(all_card_links)} cards...")
    
    final_results = []
    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        for batch_result in executor.map(process_set_batch, chunks):
            final_results.extend(batch_result)

    df_raw = pl.from_dicts(final_results, infer_schema_length=None)

    print("Compiling DataFrames")

    df_pokemon = df_raw.filter(pl.col("card_type") == 'pokemon').select(BASE_FIELDS + POKEMON_FIELDS)
    df_trainers = df_raw.filter(pl.col("card_type") == 'trainer').select(BASE_FIELDS + TRAINER_FIELDS)

    pkmn_data, pcards, ability_data, attack_data = separate_pokemon_data(df_pokemon)
    trainer_data, tcards = separate_trainer_data(df_trainers)

    cards = pl.concat([pcards, tcards]).sort(by=["set", "card"])

    print(f"Saving dataframes")

    frames = {
        "pymon" : pkmn_data,
        "abilities" : ability_data,
        "attacks" : attack_data,
        "trainers" : trainer_data,
        "cards" : cards
    }

    base_path = Path(save_path)
    base_path.mkdir(parents=True, exist_ok=True)

    for name, df in frames.items():
        path = base_path / f"{name}.parquet"
        df.write_parquet(path)
        print(f" - Exported {name} to {path}")