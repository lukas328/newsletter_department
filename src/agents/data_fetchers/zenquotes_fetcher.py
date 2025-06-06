from typing import List
import requests
import logging
from src.agents.data_fetchers.base_fetcher import BaseDataFetcher
from src.models.data_models import Quote

logger = logging.getLogger(__name__)

class ZenQuotesFetcher(BaseDataFetcher):
    """Fetcher for a daily inspirational quote from the ZenQuotes API."""

    BASE_URL = "https://zenquotes.io/api/today"

    def __init__(self):
        super().__init__(source_name="ZenQuotes")

    def fetch_data(self) -> List[Quote]:
        try:
            response = requests.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data:
                q = data[0]
                quote = Quote(text=q.get("q", ""), author=q.get("a"))
                return [quote]
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Zitats: {e}")
        return []
