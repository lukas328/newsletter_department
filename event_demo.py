from src.utils.config_loader import load_env
from src.agents.data_fetchers.eventbrite_fetcher import EventbriteFetcher
import logging

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    load_env()
    fetcher = EventbriteFetcher(query="sport OR party OR rave", categories="108,103")
    events = fetcher.fetch_data()
    for e in events:
        print(f"{e.summary} - {e.start_time} - {e.location} - {e.url}")

