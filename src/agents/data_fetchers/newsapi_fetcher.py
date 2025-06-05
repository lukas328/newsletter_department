# newsletter_project/src/agents/data_fetchers/newsapi_fetcher.py
# Datenbeschaffer für Nachrichten von NewsAPI.org.

import requests # HTTP-Anfragen
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone

# Lokale Importe
from src.agents.data_fetchers.base_fetcher import BaseDataFetcher
from src.models.data_models import RawArticle # Unser Pydantic-Modell für Rohartikel
from src.utils.config_loader import get_api_key # Zum sicheren Laden des API-Schlüssels
import json # Für das Parsen von Fehlermeldungen der API



logger = logging.getLogger(__name__)

class NewsAPIFetcher(BaseDataFetcher):
    """
    Ruft Nachrichtenartikel vom NewsAPI.org Dienst ab.
    Kann entweder den /v2/everything oder /v2/top-headlines Endpunkt verwenden.
    """
    BASE_URL = "https://newsapi.org/v2/"

    def __init__(self, 
                 api_key_name: str = "NEWSAPI_API_KEY",
                 query: Optional[str] = None, 
                 country: Optional[str] = None,
                 category: Optional[str] = None,
                 sources: Optional[str] = None, # Komma-separierte Quellen-IDs
                 language: str = "de", 
                 days_ago: int = 1, # Für 'everything' Endpunkt relevant (wie viele Tage zurück)
                 endpoint: str = "everything", # 'everything' oder 'top-headlines'
                 page_size: int = 20, # Anzahl der Artikel pro Anfrage (max. 100 für NewsAPI)
                 source_name_override: Optional[str] = None): # Für spezifische Benennung im Logging etc.
        
        effective_source_name = source_name_override if source_name_override else f"NewsAPI ({endpoint})"
        super().__init__(source_name=effective_source_name)
        
        self.api_key = get_api_key(api_key_name)
        self.query = query
        self.country = country
        self.category = category
        self.sources = sources
        self.language = language
        self.days_ago = days_ago # Wichtig für den 'from'-Parameter bei 'everything'
        self.endpoint = endpoint.lower()
        self.page_size = min(page_size, 100) # NewsAPI erlaubt max. 100

        if self.endpoint not in ["everything", "top-headlines"]:
            logger.error(f"Ungültiger NewsAPI Endpunkt '{self.endpoint}' für Quelle '{self.source_name}'.")
            raise ValueError("Ungültiger Endpunkt für NewsAPI. Muss 'everything' oder 'top-headlines' sein.")
        
        if self.endpoint == "top-headlines" and self.sources and (self.country or self.category):
            logger.warning(f"NewsAPI: Für /top-headlines wird 'sources' verwendet, 'country'/'category' werden ignoriert für Quelle '{self.source_name}'.")


    def _get_from_date_param(self) -> Optional[str]:
        """Erstellt den Datumsstring für den 'from'-Parameter des 'everything'-Endpunkts."""
        if self.endpoint == "everything":
            # NewsAPI 'from' ist das Startdatum (inklusive). 
            # Um Artikel der letzten 24h zu bekommen, ist das Datum von gestern ein guter Start.
            # Genauere "letzte 24h"-Filterung müsste nach dem Abruf erfolgen, falls nötig.
            from_date = datetime.now(timezone.utc) - timedelta(days=self.days_ago)
            return from_date.strftime("%Y-%m-%d")
        return None

    def fetch_data(self) -> List[RawArticle]:
        """Ruft Nachrichten von NewsAPI ab und gibt sie als Liste von RawArticle-Objekten zurück."""
        params: Dict[str, Any] = { # Explizite Typisierung für Klarheit
            "apiKey": self.api_key,
            "language": self.language,
            "pageSize": self.page_size,
        }

        if self.endpoint == "everything":
            if not self.query:
                logger.warning(f"Für den 'everything'-Endpunkt von '{self.source_name}' wird ein Suchbegriff ('query') dringend empfohlen, um relevante Ergebnisse zu erhalten.")
            params["q"] = self.query if self.query else "Aktuelles" # Fallback, falls kein Query
            
            from_date = self._get_from_date_param()
            if from_date:
                 params["from"] = from_date
            params["sortBy"] = "publishedAt" # oder "relevancy", "popularity"
        
        elif self.endpoint == "top-headlines":
            # Priorisierung: sources > country/category > q (für Top-Headlines)
            if self.sources:
                params["sources"] = self.sources
            elif self.country:
                params["country"] = self.country
                if self.category: 
                    params["category"] = self.category
            elif self.category: # Kategorie allein ist möglich, aber oft mit country besser
                params["category"] = self.category
            
            if self.query: # 'q' kann auch mit /top-headlines verwendet werden
                params["q"] = self.query
            
            if not (self.sources or self.country or self.category or self.query):
                logger.error(f"Für NewsAPI /top-headlines muss mindestens einer der Parameter 'sources', 'country', 'category' oder 'q' gesetzt sein für Quelle '{self.source_name}'. Es werden keine Daten abgerufen.")
                return []

        url = f"{self.BASE_URL}{self.endpoint}"
        
        # Logge Parameter ohne API-Key für Sicherheit
        params_to_log = {k: v for k, v in params.items() if k != 'apiKey'}
        logger.info(f"Frage NewsAPI ({self.source_name}) ab: {url} mit Parametern: {params_to_log}")
        
        fetched_articles: List[RawArticle] = []
        try:
            response = requests.get(url, params=params, timeout=20) # Timeout in Sekunden
            
            logger.debug(f"NewsAPI ({self.source_name}) Status Code: {response.status_code}")
            response.raise_for_status() # Löst HTTPError bei 4xx/5xx Antworten aus
            
            data = response.json()

            if data.get("status") == "error":
                logger.error(f"NewsAPI Fehler ({self.source_name}): Code '{data.get('code')}', Message '{data.get('message')}'")
                return [] # Leere Liste bei API-seitigem Fehler

            articles_data = data.get("articles", [])
            logger.info(f"NewsAPI ({self.source_name}) lieferte {data.get('totalResults', 0)} Gesamtartikel, {len(articles_data)} im aktuellen Batch.")

            for article_item in articles_data:
                try:
                    # `ensure_timezone_aware` wird vom Pydantic-Modell beim Parsen von published_at gehandhabt.
                    raw_article = RawArticle(
                        title=article_item.get("title"),
                        url=str(article_item.get("url")) if article_item.get("url") else None, # Pydantic HttpUrl braucht String
                        description=article_item.get("description"),
                        content_snippet=article_item.get("content"), # NewsAPI liefert oft nur einen Snippet hier
                        published_at=article_item.get("publishedAt"), # String wird von Pydantic geparsed
                        source_name=article_item.get("source", {}).get("name", self.source_name),
                        source_id=article_item.get("source", {}).get("id"),
                        image_url=article_item.get("urlToImage")
                    )
                    fetched_articles.append(raw_article)
                except Exception as e_article_parse: # Fängt Pydantic ValidationErrors oder andere Fehler ab
                    logger.warning(f"Überspringe Artikel von '{self.source_name}' aufgrund eines Parsing/Validierungs-Fehlers: '{article_item.get('title', 'Unbekannter Titel')}' - Fehler: {e_article_parse}", exc_info=False)
            
            logger.info(f"{len(fetched_articles)} Artikel erfolgreich von '{self.source_name}' abgerufen und als RawArticle-Objekte erstellt.")

        except requests.exceptions.HTTPError as e_http:
            error_message = f"HTTP-Fehler ({e_http.response.status_code if e_http.response else 'N/A'}) beim Abrufen von '{self.source_name}'"
            try:
                if e_http.response is not None:
                    error_details = e_http.response.json()
                    error_message += f": {error_details.get('code')} - {error_details.get('message')}"
            except json.JSONDecodeError: # Falls die Fehlerantwort kein JSON ist
                error_message += f". Rohantwort: {e_http.response.text[:200] if e_http.response else 'Kein Text'}"
            logger.error(error_message, exc_info=False)
        except requests.exceptions.RequestException as e_req: # z.B. DNS-Fehler, Verbindungsproblem
            logger.error(f"Netzwerkfehler beim Abrufen von Daten von '{self.source_name}': {e_req}", exc_info=True)
        except Exception as e_general: # Andere unerwartete Fehler
            logger.error(f"Unerwarteter Fehler beim Verarbeiten von Daten von '{self.source_name}': {e_general}", exc_info=True)
        
        return fetched_articles

