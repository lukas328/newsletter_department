from src.agents.data_fetchers.google_calendar_fetcher import GoogleCalendarFetcher
from google.oauth2 import service_account
from googleapiclient import discovery


def test_calendar_fetcher(monkeypatch, tmp_path):
    # Patch credentials and build
    class DummyCred:
        def authorize(self, http=None):
            return http

    def dummy_from_file(path, scopes=None):
        return DummyCred()

    class DummyEvents:
        def list(self, **kwargs):
            self.kwargs = kwargs
            return self

        def execute(self):
            return {
                "items": [
                    {
                        "summary": "Test",
                        "start": {"dateTime": "2025-01-01T10:00:00Z"},
                        "end": {"dateTime": "2025-01-01T11:00:00Z"},
                        "htmlLink": "http://event",
                    }
                ]
            }

    class DummyService:
        def events(self):
            return DummyEvents()

    monkeypatch.setattr(service_account.Credentials, "from_service_account_file", dummy_from_file)
    monkeypatch.setattr(discovery, "build", lambda *a, **k: DummyService())
    monkeypatch.setattr("src.agents.data_fetchers.google_calendar_fetcher.build", lambda *a, **k: DummyService())

    fetcher = GoogleCalendarFetcher("creds.json")
    events = fetcher.fetch_data()
    assert len(events) == 1
    assert events[0].summary == "Test"
