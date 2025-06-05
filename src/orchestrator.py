# newsletter_project/src/orchestrator.py
# Steuert den gesamten Ablauf der Newsletter-Generierung.

import logging
from datetime import datetime, timezone
from typing import List, Optional, Any, Dict 

from src.utils.config_loader import load_env, get_env_variable

from src.models.data_models import RawArticle, ProcessedArticle, WeatherInfo
from src.agents.data_fetchers.newsapi_fetcher import NewsAPIFetcher
from src.agents.data_fetchers.openweathermap_fetcher import OpenWeatherMapFetcher

from src.agents.data_fetchers.zenquotes_fetcher import ZenQuotesFetcher

from src.agents.llm_processors.summarizer_agent import SummarizerAgent
from src.agents.llm_processors.categorizer_agent import CategorizerAgent
from src.agents.llm_processors.article_writer_agent import ArticleWriterAgent
from src.utils.epub_utils import generate_epub
from src.agents.distributors.gdrive_uploader import GDriveUploader

logger = logging.getLogger(__name__)

class NewsletterOrchestrator:
    def __init__(self):
        load_env()
        logger.info("Initialisiere Newsletter Orchestrator...")

        blacklist_raw = get_env_variable("NEWSLETTER_SOURCE_BLACKLIST", "")
        self.source_blacklist = [s.strip().lower() for s in blacklist_raw.split(',') if s.strip()] if blacklist_raw else []
        if self.source_blacklist:
            logger.info(f"Quellen-Blacklist aktiv: {self.source_blacklist}")

        self.news_api_fetchers: List[NewsAPIFetcher] = [
            NewsAPIFetcher(query="Künstliche Intelligenz OR Technologie", language="de", endpoint="everything", days_ago=1, page_size=3, source_name_override="KI & Tech News (DE)"), # page_size reduziert für Tests
            NewsAPIFetcher(country="ch", category="technology", endpoint="top-headlines", page_size=2, source_name_override="Schweiz Tech-Schlagzeilen"),
            NewsAPIFetcher(query="global innovation OR science breakthrough", language="en", endpoint="everything", days_ago=1, page_size=3, source_name_override="Internationale Innovation (EN)")
        ]


        # Weather fetcher for Zurich
        try:
            self.weather_fetcher = OpenWeatherMapFetcher(city="Zurich")
            logger.info("OpenWeatherMapFetcher erfolgreich initialisiert.")
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung des OpenWeatherMapFetcher: {e}", exc_info=True)
            self.weather_fetcher = None

        self.quote_fetcher = ZenQuotesFetcher()

        
        try:
            self.summarizer = SummarizerAgent() 
            logger.info("SummarizerAgent erfolgreich initialisiert.")
        except Exception as e:
            logger.critical(f"Fehler bei der Initialisierung des SummarizerAgent: {e}", exc_info=True)
            self.summarizer = None
        
        try:
            # Lade Kategorien aus .env oder verwende einen Default
            categories_str = get_env_variable("NEWSLETTER_CATEGORIES", "IT & AI,Welt und Politik,Wirtschaft,Zürich Inside,Kultur und Inspiration,Der Rund um Blick")
            self.newsletter_categories = [cat.strip() for cat in categories_str.split(',')]
            if not self.newsletter_categories or not all(self.newsletter_categories): # Prüft auf leere Liste oder leere Strings
                logger.warning("Keine gültigen Kategorien gefunden. Verwende Fallback-Kategorien.")
                self.newsletter_categories = ["Allgemein"] # Fallback

            self.categorizer = CategorizerAgent(categories=self.newsletter_categories)
            logger.info(f"CategorizerAgent erfolgreich initialisiert mit Kategorien: {self.newsletter_categories}")
        except Exception as e:
            logger.critical(
                f"Fehler bei der Initialisierung des CategorizerAgent: {e}", exc_info=True
            )
            self.categorizer = None

        try:
            self.article_writer = ArticleWriterAgent()
            logger.info("ArticleWriterAgent erfolgreich initialisiert.")
        except Exception as e:
            logger.critical(
                f"Fehler bei der Initialisierung des ArticleWriterAgent: {e}", exc_info=True
            )
            self.article_writer = None

        # Wie viele Artikel sollen voll ausgeschrieben werden?
        top_n_str = get_env_variable("NEWSLETTER_TOP_ARTICLE_COUNT", "3")
        try:
            self.top_article_count = max(1, int(top_n_str))
        except ValueError:
            logger.warning(
                f"Ungültiger Wert '{top_n_str}' für NEWSLETTER_TOP_ARTICLE_COUNT. Verwende Standard 3."
            )
            self.top_article_count = 3

        logger.info("Newsletter Orchestrator initialisiert.")

    def _fetch_all_data(self) -> List[RawArticle]:
        # ... (Code bleibt gleich wie in Schritt 5) ...
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

    def _fetch_weather(self) -> List[WeatherInfo]:
        """Fetch weather forecast information."""
        if not self.weather_fetcher:
            logger.warning("Weather fetcher not available. Skipping weather data fetch.")
            return []
        try:
            return self.weather_fetcher.fetch_data()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Wetterdaten: {e}", exc_info=True)
            return []

    def _filter_blacklisted_sources(self, articles: List[RawArticle]) -> List[RawArticle]:
        """Entfernt Artikel von Quellen, die in der Blacklist stehen."""
        if not self.source_blacklist:
            return articles

        filtered: List[RawArticle] = []
        removed = 0
        for art in articles:
            src_id = (art.source_id or "").lower()
            src_name = (art.source_name or "").lower()
            if src_id in self.source_blacklist or src_name in self.source_blacklist:
                removed += 1
            else:
                filtered.append(art)

        if removed:
            logger.info(f"{removed} Artikel aufgrund der Quellen-Blacklist entfernt.")
        return filtered


    def _process_articles_with_llm(self, raw_articles: List[RawArticle]) -> List[ProcessedArticle]:
        """Verarbeitet Rohartikel mit LLM-Agenten (Zusammenfassung, dann Kategorisierung)."""
        
        # 1. Zusammenfassen
        if not self.summarizer:
            logger.error("SummarizerAgent nicht verfügbar. Überspringe Zusammenfassung.")
            # Erstelle ProcessedArticles ohne echte Zusammenfassung, aber mit Platzhalter
            summarized_articles = [
                ProcessedArticle(title=ra.title or "N/A", summary="Zusammenfassung nicht verfügbar (Summarizer-Fehler).", url=ra.url, source_name=ra.source_name, published_at=ra.published_at) 
                for ra in raw_articles
            ]
        else:
            logger.info(f"Starte LLM-Verarbeitung (Zusammenfassung) für {len(raw_articles)} Artikel...")
            summarized_articles = self.summarizer.process_batch(raw_articles)
            logger.info(f"{len(summarized_articles)} Artikel erfolgreich zusammengefasst.")

        if not summarized_articles:
            logger.warning("Keine Artikel nach der Zusammenfassung übrig.")
            return []

        # 2. Kategorisieren (nimmt die zusammengefassten Artikel)
        if not self.categorizer:
            logger.error("CategorizerAgent nicht verfügbar. Überspringe Kategorisierung.")
            categorized_articles = summarized_articles
        else:
            logger.info(
                f"Starte LLM-Verarbeitung (Kategorisierung) für {len(summarized_articles)} Artikel..."
            )
            # Der CategorizerAgent modifiziert die ProcessedArticle-Objekte direkt (fügt Kategorie hinzu)
            categorized_articles = self.categorizer.process_batch(summarized_articles)
            logger.info(f"{len(categorized_articles)} Artikel erfolgreich kategorisiert.")

        # 3. Ausformulierten Artikeltext generieren
        if self.article_writer:
            # Nur die Top-N Artikel anhand des Relevanzscores ausformulieren
            sorted_articles = sorted(
                categorized_articles,
                key=lambda a: a.relevance_score or 0,
                reverse=True,
            )
            top_articles = sorted_articles[: self.top_article_count]

            logger.info(
                f"Starte LLM-Verarbeitung (Artikelerstellung) für {len(top_articles)} von {len(categorized_articles)} Artikeln (Top {self.top_article_count})."
            )
            article_texts = self.article_writer.process_batch(top_articles)
            for art, text in zip(top_articles, article_texts):
                art.article_text = text
                if art.llm_processing_details is None:
                    art.llm_processing_details = {}
                art.llm_processing_details["writer_model"] = self.article_writer.model_name
        else:
            logger.error("ArticleWriterAgent nicht verfügbar. Überspringe Artikelerstellung.")

        return categorized_articles


    def run_pipeline(self) -> Optional[str]:
        logger.info("Newsletter-Generierungspipeline gestartet durch Orchestrator.")
        start_time = datetime.now(timezone.utc)

        # --- Schritt 1: Daten sammeln ---
        raw_articles = self._fetch_all_data()
        if not raw_articles:
            logger.warning("Keine Rohartikel zum Verarbeiten gefunden.")
            return "Keine Daten gefunden"
        raw_articles = self._filter_blacklisted_sources(raw_articles)
        if not raw_articles:
            logger.warning("Alle Artikel wurden von der Blacklist herausgefiltert.")
            return "Keine Daten nach Blacklist"
        logger.info(f"{len(raw_articles)} Rohartikel gesammelt (nach Filter).")
        for i, article in enumerate(raw_articles[:1]):  # Nur den ersten Artikel zur Kontrolle loggen
            logger.debug(
                f"  Rohartikel {i+1}: {article.title} (Quelle: {article.source_name}, Datum: {article.published_at})"
            )

        # --- Schritt 2: Daten verarbeiten mit LLMs ---
        processed_articles = self._process_articles_with_llm(raw_articles)
        if not processed_articles:
            logger.warning("Keine Artikel nach der LLM-Verarbeitung. Pipeline wird beendet.")
            return "Keine verarbeiteten Daten nach LLM-Stufen"
        logger.info(f"{len(processed_articles)} Artikel nach LLM-Verarbeitung vorhanden.")
        for i, article in enumerate(processed_articles[:1]): # Ersten verarbeiteten Artikel loggen
            logger.debug(f"  Verarbeiteter Artikel {i+1}: '{article.title}' - Zusammenfassung (erste 50 Zeichen): '{article.summary[:50]}...' - Kategorie: {article.category}")

        # --- Schritt 3: Daten evaluieren (Platzhalter) ---
        final_items_for_newsletter = processed_articles

        weather_infos = self._fetch_weather()

        quote: Optional[Quote] = None
        try:
            quotes = self.quote_fetcher.fetch_data()
            if quotes:
                quote = quotes[0]
        except Exception as e:
            logger.error(f"Fehler beim Abrufen des Zitats: {e}", exc_info=True)


        # --- Schritt 4: Newsletter komponieren (Platzhalter) ---
        output_format = get_env_variable("NEWSLETTER_OUTPUT_FORMAT", "txt").lower()

        if output_format == "epub":
            newsletter_output_path = "tmp/newsletter.epub"
            try:
                articles_per_page = int(get_env_variable("EPUB_ARTICLES_PER_PAGE", "1"))
                use_a4_css = get_env_variable("EPUB_USE_A4_CSS", "false").lower() == "true"
                generate_epub(
                    final_items_for_newsletter,
                    newsletter_output_path,
                    articles_per_page=articles_per_page,
                    use_a4_css=use_a4_css,

                    weather_infos=weather_infos,
                    quote_of_the_day=quote.text if quote else None,
                    quote_author=quote.author if quote else None,

                )
                logger.info(f"EPUB erstellt unter: {newsletter_output_path}")

                creds = get_env_variable("GOOGLE_DRIVE_CREDENTIALS_JSON")
                if creds:
                    folder_id = get_env_variable("GOOGLE_DRIVE_FOLDER_ID")
                    try:
                        uploader = GDriveUploader(creds)
                        file_id = uploader.upload_file(newsletter_output_path, folder_id)
                        logger.info(f"EPUB in Google Drive hochgeladen. File ID: {file_id}")
                    except Exception as e_up:
                        logger.error(f"Fehler beim Hochladen zu Google Drive: {e_up}", exc_info=True)
            except Exception as e_epub:
                logger.error(f"Fehler beim Erstellen des EPUB: {e_epub}", exc_info=True)
        else:
            newsletter_output_path = "tmp/platzhalter_newsletter_mit_kategorien.txt"
            try:
                with open(newsletter_output_path, "w", encoding="utf-8") as f:
                    f.write(f"Platzhalter-Newsletter - Erstellt am: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
                    f.write("===============================================================\n\n")
                    if quote:
                        f.write(f"Zitat des Tages: {quote.text}")
                        if quote.author:
                            f.write(f" - {quote.author}")
                        f.write("\n\n")
                    if final_items_for_newsletter:
                        for item in final_items_for_newsletter:
                            f.write(f"Titel: {item.title if item.title else 'Kein Titel'}\n")
                            f.write(f"Quelle: {item.source_name if item.source_name else 'Unbekannt'}\n")
                            f.write(f"Kategorie: {item.category}\n")
                            f.write(f"URL: {str(item.url) if item.url else 'Keine URL'}\n")
                            f.write(f"Datum: {item.published_at.strftime('%Y-%m-%d %H:%M') if item.published_at else 'Kein Datum'}\n")
                            f.write(f"ZUSAMMENFASSUNG: {item.summary}\n")
                            f.write("---------------------------------------------------------------\n")
                    else:
                        f.write("Keine Artikel für diesen Newsletter gefunden.\n")
                logger.info(f"Platzhalter-Newsletter (mit Kategorien) erstellt unter: {newsletter_output_path}")
            except Exception as e:
                logger.error(f"Fehler beim Schreiben des Platzhalter-Newsletters: {e}", exc_info=True)
                newsletter_output_path = "Fehler beim Schreiben"

        # --- Schritt 5: Newsletter verteilen (Platzhalter) ---
        # ... (bleibt gleich) ...

        pipeline_duration = datetime.now(timezone.utc) - start_time
        logger.info(f"Newsletter-Pipeline in {pipeline_duration} abgeschlossen (Orchestrator).")
        return newsletter_output_path
