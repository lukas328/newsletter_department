from src.agents.data_fetchers.zenquotes_fetcher import ZenQuotesFetcher
from src.models.data_models import Quote
import requests

class DummyResp:
    def __init__(self, data):
        self._data = data
        self.status_code = 200
    def raise_for_status(self):
        pass
    def json(self):
        return self._data

def test_fetch_quote(monkeypatch):
    def fake_get(url, timeout=10):
        return DummyResp([{"q": "Be yourself", "a": "Anon"}])
    monkeypatch.setattr(requests, "get", fake_get)
    fetcher = ZenQuotesFetcher()
    quotes = fetcher.fetch_data()
    assert len(quotes) == 1
    q = quotes[0]
    assert isinstance(q, Quote)
    assert q.text == "Be yourself"
    assert q.author == "Anon"
