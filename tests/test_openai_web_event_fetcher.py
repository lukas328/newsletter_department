from src.agents.data_fetchers.openai_web_event_fetcher import OpenAIWebEventFetcher
from src.models.data_models import Event

class DummyResp:
    def __init__(self, text):
        self.output_text = text

class DummyClient:
    def __init__(self, *args, **kwargs):
        pass
    class responses:
        @staticmethod
        def create(model=None, tools=None, input=None, temperature=0.2):
            data = '[{"title": "Test Event", "start_time": "2025-01-01", "url": "http://example.com", "location": "Zurich"}]'
            return DummyResp(data)


def test_fetch_events(monkeypatch):
    monkeypatch.setattr("src.agents.data_fetchers.openai_web_event_fetcher.OpenAI", DummyClient)
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    fetcher = OpenAIWebEventFetcher(query="test")
    events = fetcher.fetch_data()
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert events[0].summary == "Test Event"
