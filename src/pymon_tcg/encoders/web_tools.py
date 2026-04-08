from selectolax.parser import HTMLParser


def scrape_card_print(tree: HTMLParser) -> dict:
    """
    Scrapes the HTML for card print data

    :param tree: HTML tree

    :returns: dictionary of the card print data (set, card, rarity)
    """

    prints_current = tree.css('.prints-current-details')[0]
    card_set_raw = prints_current.css(".text-lg")[0].text()
    num_rare_raw = prints_current.text()[len(card_set_raw):]

    card_set = card_set_raw.strip().split("(")[-1].split(")")[0]
    num_rare = num_rare_raw.strip().lower().split(" ")
    num = int(num_rare[0][1:])
    rarity = num_rare[-1]

    return {
        "set": card_set,
        "card": num,
        "rarity": rarity,
    }