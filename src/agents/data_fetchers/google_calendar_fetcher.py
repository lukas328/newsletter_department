import logging
from datetime import datetime, timezone
from typing import List

from google.oauth2 import service_account
from googleapiclient.discovery import build

from src.agents.data_fetchers.base_fetcher import BaseDataFetcher
from src.models.data_models import Event

logger = logging.getLogger(__name__)


class GoogleCalendarFetcher(BaseDataFetcher):
    """Fetches upcoming events from a Google Calendar using a service account."""

    def __init__(self, credentials_path: str, calendar_id: str = "primary", max_results: int = 3):
        super().__init__(source_name="Google Calendar")
        self.calendar_id = calendar_id
        self.max_results = max_results
        scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
        try:
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )
            self.service = build("calendar", "v3", credentials=credentials)
        except Exception as e:  # pragma: no cover - simple init wrapper
            logger.error(f"Fehler beim Initialisieren des Google Calendar Clients: {e}")
            raise

    def fetch_data(self) -> List[Event]:
        """Return upcoming calendar events as Event objects."""
        now = datetime.now(timezone.utc).isoformat()
        try:
            response = (
                self.service.events()
                .list(
                    calendarId=self.calendar_id,
                    timeMin=now,
                    maxResults=self.max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Kalendereinträge: {e}")
            return []

        events: List[Event] = []
        for item in response.get("items", []):
            start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
            end = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
            try:
                evt = Event(
                    summary=item.get("summary", "(Kein Titel)"),
                    start_time=start,
                    end_time=end,
                    location=item.get("location"),
                    description=item.get("description"),
                    url=item.get("htmlLink"),
                    source=self.source_name,
                )
                events.append(evt)
            except Exception as e_parse:  # pragma: no cover - validation safety
                logger.warning(
                    f"Überspringe Kalendereintrag '{item.get('summary')}' wegen Fehler: {e_parse}"
                )
        return events
