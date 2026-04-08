from .encoders.web_loader import scrape_for_data
from .encoders.vectorize import vectorize_raw_data

def build(raw: str = "data/raw", vectors: str = "data/encoded") -> None:
    scrape_for_data()
    vectorize_raw_data()