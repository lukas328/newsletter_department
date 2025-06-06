from src.agents.data_fetchers.serpapi_event_fetcher import SerpApiEventFetcher
from src.models.data_models import Event
import requests
import os

class DummyResp:
    def __init__(self, data):
        self.data = data
        self.status_code = 200
    def raise_for_status(self):
        pass
    def json(self):
        return self.data


def test_fetch_events(monkeypatch):
    def fake_get(url, params=None, timeout=20):
        return DummyResp({
            "events_results": [
                {
                    "title": "Test Event",
                    "date": {"start_date": "2025-01-01"},
                    "link": "http://example.com",
                    "address": "Zurich"
                }
            ]
        })
    monkeypatch.setattr(requests, "get", fake_get)
    os.environ["SERPAPI_API_KEY"] = "dummy"
    fetcher = SerpApiEventFetcher(query="test", api_key_env="SERPAPI_API_KEY")
    events = fetcher.fetch_data()
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert events[0].summary == "Test Event"
