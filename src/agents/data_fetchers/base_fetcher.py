# newsletter_project/src/agents/data_fetchers/base_fetcher.py
# Abstrakte Basisklasse für alle Datenbeschaffer-Agenten.

from abc import ABC, abstractmethod
from typing import List, Any # Any wird verwendet, da verschiedene Fetcher unterschiedliche Pydantic-Modelle zurückgeben können
import logging

logger = logging.getLogger(__name__)

class BaseDataFetcher(ABC):
    """
    Abstrakte Basisklasse für Agenten, die Daten von externen Quellen abrufen.
    """
    def __init__(self, source_name: str):
        """
        Initialisiert den Fetcher mit einem Namen für die Quelle.
        Args:
            source_name (str): Ein identifizierbarer Name für die Datenquelle 
                               (z.B. "NewsAPI-Technology", "Tagesschau RSS").
        """
        self.source_name = source_name
        logger.info(f"Initialisiere Datenbeschaffer für Quelle: '{self.source_name}'.")

    @abstractmethod
    def fetch_data(self) -> List[Any]:
        """
        Abstrakte Methode zum Abrufen von Daten.
        Muss von abgeleiteten Klassen implementiert werden.

        Returns:
            List[Any]: Eine Liste von abgerufenen Datenelementen. 
                       Die Elemente sollten Instanzen unserer Pydantic-Modelle sein 
                       (z.B. RawArticle, Event, etc.).
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(source_name='{self.source_name}')>"