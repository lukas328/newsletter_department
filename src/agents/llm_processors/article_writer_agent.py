# newsletter_project/src/agents/llm_processors/article_writer_agent.py
"""LLM-Agent, der einen ganzen Zeitungsartikel generiert.

Dieser Agent nutzt das OpenAI SDK mit dem ``web_search_preview`` Tool,
um auf Basis eines Links und einer Zusammenfassung einen ausgearbeiteten
Artikel zu verfassen. Er erwartet ein :class:`ProcessedArticle` Objekt
und gibt den generierten Artikeltext zurück.
"""

from typing import List
import logging
from openai import OpenAI

from src.models.data_models import ProcessedArticle
from src.utils.config_loader import get_api_key

logger = logging.getLogger(__name__)

class ArticleWriterAgent:
    """Erzeugt aus einem :class:`ProcessedArticle` einen ausgeschriebenen Artikel."""

    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.2):
        api_key = get_api_key("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
        self.temperature = temperature
        logger.info(
            f"ArticleWriterAgent initialisiert mit Modell '{self.model_name}' und Temperatur {self.temperature}."
        )

    def _build_prompt(self, article: ProcessedArticle) -> str:
        """Erstellt das Prompt für die LLM-Anfrage."""
        url_part = f"URL: {article.url}\n" if article.url else ""
        published = (
            article.published_at.strftime("%Y-%m-%d %H:%M") if article.published_at else "Unbekannt"
        )
        prompt = (
            "Gibt mir einen gut geschriebenen Zeitungsartikel basierend auf folgenden Informationen:\n"
            f"Titel: {article.title}\n"
            f"Quelle: {article.source_name or 'Unbekannt'}\n"
            f"Datum: {published}\n"
            f"{url_part}"
            "Zusammenfassung des Inhalts:\n"
            f"{article.summary}\n"
        )
        return prompt

    def write_article(self, article: ProcessedArticle) -> str:
        """Generiert den Artikeltext."""
        prompt = self._build_prompt(article)
        try:
            response = self.client.responses.create(
                model=self.model_name,
                tools=[{"type": "web_search_preview"}],
                input=prompt,
                temperature=self.temperature,
            )
            text = response.output_text.strip()
            logger.debug("ArticleWriterAgent Antwort erhalten.")
            return text
        except Exception as e:
            logger.error(f"Fehler beim Generieren des Artikels: {e}", exc_info=True)
            return "Artikel konnte nicht generiert werden."

    def process_batch(self, articles: List[ProcessedArticle]) -> List[str]:
        """Schreibt für mehrere Artikel jeweils einen vollwertigen Text."""
        results: List[str] = []
        for art in articles:
            results.append(self.write_article(art))
        return results
