import logging
from typing import List
import requests

from src.agents.data_fetchers.base_fetcher import BaseDataFetcher
from src.models.data_models import Artwork
from src.utils.config_loader import get_env_variable

logger = logging.getLogger(__name__)

class EuropeanaFetcher(BaseDataFetcher):
    """Ruft Kunstwerke über die Europeana API ab."""

    BASE_URL = "https://api.europeana.eu/record/v2/search.json"

    def __init__(self, query: str, rows: int = 1, api_key_env: str = "EUROPEANA_API_KEY"):
        super().__init__(source_name="Europeana")
        self.query = query
        self.rows = rows
        self.api_key = get_env_variable(api_key_env, "apidemo")

    def fetch_data(self) -> List[Artwork]:
        params = {"wskey": self.api_key, "query": self.query, "rows": self.rows}
        artworks: List[Artwork] = []
        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("items", []):
                title = (item.get("title") or [None])[0]
                artist = (item.get("dcCreator") or [None])[0]
                preview = (item.get("edmPreview") or [None])[0]
                location = (item.get("dataProvider") or [None])[0]
                epoch = (item.get("year") or [None])[0]
                artworks.append(
                    Artwork(
                        title=title or "Unbekannt",
                        image_url=preview,
                        artist=artist,
                        location=location,
                        epoch=str(epoch) if epoch else None,
                        europeana_id=item.get("id"),
                    )
                )
            logger.info(f"Europeana lieferte {len(artworks)} Ergebnisse für '{self.query}'.")
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Europeana-Daten: {e}", exc_info=True)
        return artworks
