# newsletter_project/src/orchestrator.py
# Steuert den gesamten Ablauf der Newsletter-Generierung.

import logging
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict 

from src.utils.config_loader import load_env, get_env_variable 
from src.models.data_models import RawArticle, ProcessedArticle # ProcessedArticle hinzugefügt
from src.agents.data_fetchers.newsapi_fetcher import NewsAPIFetcher 
from src.agents.llm_processors.summarizer_agent import SummarizerAgent # Summarizer importiert

logger = logging.getLogger(__name__)

class NewsletterOrchestrator:
    def __init__(self):
        load_env() 
        logger.info("Initialisiere Newsletter Orchestrator...")

        self.news_api_fetchers: List[NewsAPIFetcher] = [
            NewsAPIFetcher(query="Künstliche Intelligenz OR Technologie", language="de", endpoint="everything", days_ago=1, page_size=5, source_name_override="KI & Tech News (DE)"), # page_size reduziert für Tests
            NewsAPIFetcher(country="ch", category="technology", endpoint="top-headlines", page_size=3, source_name_override="Schweiz Tech-Schlagzeilen"), # spezifischer
            NewsAPIFetcher(query="global innovation OR science breakthrough", language="en", endpoint="everything", days_ago=1, page_size=5, source_name_override="Internationale Innovation (EN)")
        ]
        
        # Initialisiere den Summarizer Agent
        try:
            self.summarizer = SummarizerAgent() 
            logger.info("SummarizerAgent erfolgreich initialisiert.")
        except Exception as e:
            logger.critical(f"Fehler bei der Initialisierung des SummarizerAgent: {e}", exc_info=True)
            self.summarizer = None # Setze auf None, damit die Pipeline es handhaben kann

        # Platzhalter für weitere Agenten
        # self.categorizer = ...
        # self.evaluator = ...
        # self.composer = ...
        # self.distributor = ...

        logger.info(f"Newsletter Orchestrator initialisiert.")

    def _fetch_all_data(self) -> List[RawArticle]:
        all_fetched_articles: List[RawArticle] = []
        logger.info("Starte Datensammlung von allen konfigurierten Quellen...")
        for fetcher in self.news_api_fetchers:
            try:
                logger.info(f"Rufe Daten von Fetcher '{fetcher.source_name}' ab...")
                articles = fetcher.fetch_data()
                if articles:
                    all_fetched_articles.extend(articles)
                    logger.info(f"{len(articles)} Artikel von '{fetcher.source_name}' erfolgreich abgerufen.")
                else:
                    logger.info(f"Keine Artikel von '{fetcher.source_name}' abgerufen.")
            except Exception as e:
                logger.error(f"Fehler beim Abrufen von Daten durch Fetcher '{fetcher.source_name}': {e}", exc_info=True)
        logger.info(f"Insgesamt {len(all_fetched_articles)} Rohartikel von allen Quellen gesammelt.")
        return all_fetched_articles

    def _process_articles_with_llm(self, raw_articles: List[RawArticle]) -> List[ProcessedArticle]:
        """Verarbeitet Rohartikel mit LLM-Agenten (z.B. Zusammenfassung)."""
        if not self.summarizer:
            logger.error("SummarizerAgent nicht verfügbar. Überspringe LLM-Verarbeitung.")
            # Wandle RawArticles in ProcessedArticles ohne Zusammenfassung um, oder gib leere Liste zurück
            return [
                ProcessedArticle(title=ra.title or "N/A", summary="Zusammenfassung nicht verfügbar (Summarizer-Fehler).", url=ra.url, source_name=ra.source_name, published_at=ra.published_at) 
                for ra in raw_articles
            ]

        logger.info(f"Starte LLM-Verarbeitung (Zusammenfassung) für {len(raw_articles)} Artikel...")
        # Rufe die Batch-Verarbeitungsmethode des Summarizers auf
        processed_articles = self.summarizer.process(raw_articles)
        logger.info(f"{len(processed_articles)} Artikel erfolgreich zusammengefasst.")
        return processed_articles


    def run_pipeline(self) -> Optional[str]:
        logger.info("Newsletter-Generierungspipeline gestartet durch Orchestrator.")
        start_time = datetime.now(timezone.utc)

        # --- Schritt 1: Daten sammeln ---
        logger.info("Phase 1: Daten sammeln...")
        raw_articles = self._fetch_all_data()
        
        if not raw_articles:
            logger.warning("Keine Rohartikel zum Verarbeiten gefunden. Pipeline wird beendet.")
            # ... (Rest der Fehlerbehandlung und Rückgabe)
            return "Keine Daten gefunden"
        
        logger.info(f"{len(raw_articles)} Rohartikel gesammelt.")
        for i, article in enumerate(raw_articles[:2]): # Erste 2 Artikel zur Kontrolle loggen
            logger.debug(f"  Rohartikel {i+1}: {article.title} (Quelle: {article.source_name}, Datum: {article.published_at})")

        # --- Schritt 2: Daten verarbeiten mit LLMs ---
        logger.info("Phase 2: Daten mit LLMs verarbeiten (Zusammenfassen)...")
        processed_articles = self._process_articles_with_llm(raw_articles)
        
        if not processed_articles:
            logger.warning("Keine Artikel nach der LLM-Verarbeitung (Zusammenfassung). Pipeline wird beendet.")
            return "Keine verarbeiteten Daten nach Zusammenfassung"
            
        logger.info(f"{len(processed_articles)} Artikel nach Zusammenfassung vorhanden.")
        for i, article in enumerate(processed_articles[:2]): # Erste 2 verarbeitete Artikel loggen
            logger.debug(f"  Verarbeiteter Artikel {i+1}: {article.title} - Zusammenfassung (erste 50 Zeichen): '{article.summary[:50]}...'")
        
        # --- Schritt 3: Daten evaluieren (Platzhalter) ---
        final_items_for_newsletter = processed_articles # Vorerst die zusammengefassten Artikel verwenden

        # --- Schritt 4: Newsletter komponieren (Platzhalter) ---
        logger.info("Phase 4: Newsletter komponieren (Platzhalter)...")
        newsletter_output_path = "tmp/platzhalter_newsletter_mit_zusammenfassungen.txt" 
        try:
            with open(newsletter_output_path, "w", encoding="utf-8") as f:
                f.write(f"Platzhalter-Newsletter - Erstellt am: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
                f.write("==============================================================\n\n")
                if final_items_for_newsletter:
                    for item in final_items_for_newsletter: # Iteriere jetzt über ProcessedArticle-Objekte
                        f.write(f"Titel: {item.title if item.title else 'Kein Titel'}\n")
                        f.write(f"Quelle: {item.source_name if item.source_name else 'Unbekannt'}\n")
                        f.write(f"URL: {str(item.url) if item.url else 'Keine URL'}\n")
                        f.write(f"Datum: {item.published_at.strftime('%Y-%m-%d %H:%M') if item.published_at else 'Kein Datum'}\n")
                        f.write(f"ZUSAMMENFASSUNG: {item.summary}\n")
                        f.write("--------------------------------------------------------------\n")
                else:
                    f.write("Keine Artikel für diesen Newsletter gefunden.\n")
            logger.info(f"Platzhalter-Newsletter (mit Zusammenfassungen) erstellt unter: {newsletter_output_path}")
        except Exception as e:
            logger.error(f"Fehler beim Schreiben des Platzhalter-Newsletters: {e}", exc_info=True)
            newsletter_output_path = "Fehler beim Schreiben"

        # --- Schritt 5: Newsletter verteilen (Platzhalter) ---
        # ... (bleibt gleich) ...

        pipeline_duration = datetime.now(timezone.utc) - start_time
        logger.info(f"Newsletter-Pipeline in {pipeline_duration} abgeschlossen (Orchestrator).")
        return newsletter_output_path