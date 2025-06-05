"""Kleines Beispielskript zum Abrufen eines Kunstwerks von Europeana
und zur Erstellung einer Kurzbeschreibung mittels LLM."""

import logging
import requests

from src.utils.logging_setup import setup_logging
from src.utils.config_loader import load_env
from src.agents.data_fetchers.europeana_fetcher import EuropeanaFetcher
from src.agents.llm_processors.art_description_agent import ArtDescriptionAgent


def main() -> None:
    load_env()
    setup_logging()
    logger = logging.getLogger(__name__)

    fetcher = EuropeanaFetcher(query="Monet", rows=1)
    artworks = fetcher.fetch_data()
    if not artworks:
        logger.error("Keine Kunstwerke gefunden.")
        return

    art = artworks[0]
    logger.info(f"Gefundenes Kunstwerk: {art.title}")

    if art.image_url:
        resp = requests.get(art.image_url)
        with open("tmp/europeana_preview.jpg", "wb") as f:
            f.write(resp.content)
        logger.info("Vorschaubild gespeichert unter tmp/europeana_preview.jpg")

    agent = ArtDescriptionAgent()
    description = agent.describe_artwork(art)
    print("Beschreibung:\n" + description)


if __name__ == "__main__":
    main()
