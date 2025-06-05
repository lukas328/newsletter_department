from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from google.oauth2 import service_account
from googleapiclient.discovery import build

from src.agents.data_fetchers.base_fetcher import BaseDataFetcher
from src.models.data_models import Birthday

logger = logging.getLogger(__name__)


class BirthdaySheetFetcher(BaseDataFetcher):
    """Fetch birthdays from a Google Sheet."""

    def __init__(self, credentials_path: str, sheet_id: str, range_name: str = "A2:B"):
        super().__init__(source_name="Google Sheets")
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=scopes
        )
        self.service = build("sheets", "v4", credentials=credentials)
        self.sheet_id = sheet_id
        self.range_name = range_name

    def _parse_date(self, date_str: str) -> Optional[Tuple[int, int]]:
        if not date_str:
            return None
        formats = [
            "%Y-%m-%d",
            "%d.%m.%Y",
            "%d.%m.%y",
            "%d.%m.",
            "%d.%m",
            "%m/%d/%Y",
            "%m/%d",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.month, dt.day
            except ValueError:
                continue
        return None

    def fetch_data(self) -> List[Birthday]:
        result = (
            self.service.spreadsheets()
            .values()
            .get(spreadsheetId=self.sheet_id, range=self.range_name)
            .execute()
        )
        values = result.get("values", [])
        birthdays: List[Birthday] = []
        for row in values:
            if not row:
                continue
            name = row[0].strip() if row[0] else ""
            date_str = row[1].strip() if len(row) > 1 else ""
            if not name or not date_str:
                continue
            md = self._parse_date(date_str)
            if md:
                month, day = md
                birthdays.append(
                    Birthday(
                        name=name,
                        date_month=month,
                        date_day=day,
                        original_date_info=date_str,
                        source=self.source_name,
                    )
                )
            else:
                logger.warning(
                    "Konnte Datum '%s' für '%s' nicht parsen.", date_str, name
                )
        logger.info("%d Geburtstage aus Google Sheets geladen", len(birthdays))
        return birthdays

