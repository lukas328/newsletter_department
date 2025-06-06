import logging
import json
from typing import List
from openai import OpenAI

from .base_fetcher import BaseDataFetcher
from src.models.data_models import Event
from src.utils.config_loader import get_api_key

logger = logging.getLogger(__name__)

class OpenAIWebEventFetcher(BaseDataFetcher):
    """Fetches upcoming events using OpenAI's web search tool."""

    def __init__(self, query: str = "events in Zurich", model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        super().__init__(source_name="OpenAI Web Search")
        self.query = query
        self.model_name = model_name
        self.temperature = temperature
        api_key = get_api_key("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)

    def fetch_data(self) -> List[Event]:
        prompt = (
            "Search the web for upcoming events for the following search query: "
            f"'{self.query}'. "
            "Return up to 5 events as a JSON list with keys 'title', 'start_time', 'location', and 'url'."
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
            logger.error("Error fetching events via OpenAI web search: %s", exc, exc_info=True)
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
                    source="OpenAI Web Search",
                )
                events.append(evt)
            except Exception as e_item:
                logger.warning("Skipping event due to error: %s", e_item)
        logger.info("Fetched %d events from OpenAI web search", len(events))
        return events
