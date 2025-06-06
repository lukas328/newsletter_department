import logging
import json
from typing import List
from openai import OpenAI

from .base_fetcher import BaseDataFetcher
from src.models.data_models import Event
from src.utils.config_loader import get_api_key

logger = logging.getLogger(__name__)

class OpenAILinkEventFetcher(BaseDataFetcher):
    """Fetch events by searching specific websites using OpenAI's web search tool."""

    def __init__(self, urls: List[str], model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        super().__init__(source_name="OpenAI Link Search")
        self.urls = urls
        self.model_name = model_name
        self.temperature = temperature
        api_key = get_api_key("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def _search_site(self, url: str) -> List[Event]:
        prompt = (
            f"Search {url} for upcoming events. "
            "Return up to 3 events as a JSON list with keys 'title', 'start_time', 'location', and 'url'."
        )
        try:
            response = self.client.responses.create(
                model=self.model_name,
                tools=[{"type": "web_search_preview"}],
                input=prompt,
                temperature=self.temperature,
            )
            text = response.output_text.strip()
            data = json.loads(text)
        except Exception as exc:
            logger.error("Error searching %s via OpenAI web search: %s", url, exc, exc_info=True)
            return []

        events: List[Event] = []
        for item in data:
            try:
                evt = Event(
                    summary=item.get("title") or item.get("summary"),
                    start_time=item.get("start_time"),
                    end_time=item.get("end_time"),
                    location=item.get("location"),
                    description=item.get("description"),
                    url=item.get("url"),
                    source=f"OpenAI Link Search ({url})",
                )
                events.append(evt)
            except Exception as e_item:
                logger.warning("Skipping event from %s due to error: %s", url, e_item)
        return events

    def fetch_data(self) -> List[Event]:
        all_events: List[Event] = []
        for url in self.urls:
            events = self._search_site(url)
            all_events.extend(events)
        logger.info("Fetched %d events via OpenAI link search", len(all_events))
        return all_events
