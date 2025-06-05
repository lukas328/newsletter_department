"""Todoist data fetcher."""
from typing import List, Optional
import requests
import logging

from src.agents.data_fetchers.base_fetcher import BaseDataFetcher
from src.models.data_models import TodoItem
from src.utils.config_loader import get_api_key

logger = logging.getLogger(__name__)


class TodoistFetcher(BaseDataFetcher):
    """Fetches tasks from the Todoist REST API."""

    API_URL = "https://api.todoist.com/rest/v2/tasks"

    def __init__(self, api_token_name: str = "TODOIST_API_TOKEN", project_id: Optional[str] = None):
        super().__init__(source_name="Todoist")
        self.api_token = get_api_key(api_token_name)
        self.project_id = project_id

    def fetch_data(self) -> List[TodoItem]:
        headers = {"Authorization": f"Bearer {self.api_token}"}
        params = {}
        if self.project_id:
            params["project_id"] = self.project_id
        try:
            resp = requests.get(self.API_URL, headers=headers, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.error("Failed to fetch Todoist tasks: %s", exc, exc_info=True)
            return []

        todos: List[TodoItem] = []
        for item in data:
            try:
                todos.append(TodoItem(id=item.get("id"), content=item.get("content")))
            except Exception as e_item:
                logger.warning("Skipping todo item due to error: %s", e_item)
        logger.info("Fetched %d Todoist tasks", len(todos))
        return todos
