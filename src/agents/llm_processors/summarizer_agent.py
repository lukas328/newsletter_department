# newsletter_project/src/agents/llm_processors/summarizer_agent.py
# LLM-Agent zum Zusammenfassen von Texten (z.B. Artikel).

from typing import List, Union, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser # Einfacher Parser für String-Antworten
from src.models.data_models import RawArticle, ProcessedArticle # Unsere Datenmodelle
from .base_processor import BaseLLMProcessor # Unsere Basisklasse
import logging

logger = logging.getLogger(__name__)

class SummarizerAgent(BaseLLMProcessor):
    """
    Ein LLM-Agent, der darauf spezialisiert ist, Texte (insbesondere Artikel) zusammenzufassen.
    """
    def __init__(self, 
                 model_name: Optional[str] = None, # Wird vom BaseLLMProcessor mit Default belegt
                 temperature: float = 1): # Niedrigere Temperatur für faktenbasierte Zusammenfassungen
        super().__init__(model_name=model_name, temperature=temperature)
        
        # Definiere das Prompt-Template für die Zusammenfassung.
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", "Du bist ein Experte im Verfassen prägnanter Nachrichten-Zusammenfassungen."),
            ("human",
             """
Bitte fasse den folgenden Text für einen Newsletter zusammen. Die Zusammenfassung sollte die Kernbotschaft in 2-4 prägnanten Sätzen wiedergeben.
Konzentriere dich auf die wichtigsten Fakten und Implikationen. Vermeide Füllwörter und unnötige Details.
Gib NUR die reine Zusammenfassung zurück, ohne zusätzliche Einleitungen, Höflichkeitsfloskeln, Entschuldigungen oder Kommentare wie "Hier ist die Zusammenfassung:".

ARTIKELTITEL: {title}
VERFÜGBARER TEXT ZUM ARTIKEL (kann Beschreibung oder Inhaltsauszug sein): 
---
{text_to_summarize}
---

ZUSAMMENFASSUNG:""")
        ])
        
        # Erstelle die LangChain-Kette: Prompt -> LLM -> Output Parser
        # StrOutputParser gibt die LLM-Antwort direkt als String zurück.
        self.chain = self.prompt_template | self.llm | StrOutputParser()
        logger.info(f"SummarizerAgent Kette initialisiert mit Modell '{self.model_name}'.")

    def _get_text_for_summarization(self, article: RawArticle) -> str:
        """Wählt den besten verfügbaren Text (content_snippet oder description) für die Zusammenfassung aus."""
        text_parts_in_preference_order = [
            article.content_snippet, # Bevorzuge längeren Inhalt, falls vorhanden
            article.description
        ]
        
        for text_part in text_parts_in_preference_order:
            if text_part and len(text_part.strip()) > 30: # Mindestlänge für einen sinnvollen Text
                return text_part.strip()
        
        # Fallback, wenn weder content noch description brauchbar sind
        logger.warning(f"Weder content_snippet noch description ist ausreichend lang für Artikel: '{article.title}'. Verwende nur den Titel.")
        return article.title if article.title else ""


    def summarize_article_text(self, title: Optional[str], text_content: str) -> str:
        """Fasst einen gegebenen Text basierend auf einem Titel zusammen."""
        if not text_content or len(text_content.strip()) < 20: # Mindestlänge für sinnvollen Input
            logger.warning(f"Zu wenig Inhalt für Titel '{title}' zum Zusammenfassen. Gebe leere Zusammenfassung zurück.")
            return "Keine Zusammenfassung möglich (unzureichender Inhalt)."

        logger.debug(f"Erstelle Zusammenfassung für Titel: '{title}' (Textlänge: {len(text_content)} Zeichen)")
        try:
            # Begrenze die Länge des Inputs, um Token-Limits und Kosten zu managen.
            # Zeichenlänge ist eine Annäherung. GPT-Modelle haben begrenzte Token-Limits.
            max_input_chars_for_llm = 4000 # Kann je nach Modell angepasst werden
            
            summary_result = self.chain.invoke({
                "title": title or "Kein Titel",
                "text_to_summarize": text_content[:max_input_chars_for_llm] 
            })
            
            logger.debug(f"Zusammenfassung für '{title}' erfolgreich vom LLM erhalten.")
            return summary_result.strip() if summary_result else "Zusammenfassung konnte nicht erstellt werden (leere LLM-Antwort)."
        except Exception as e:
            logger.error(f"Fehler beim Zusammenfassen des Textes für Titel '{title}': {e}", exc_info=True)
            return "Zusammenfassung fehlgeschlagen (LLM-Fehler)."


    def process_article(self, article: RawArticle) -> ProcessedArticle:
        """
        Verarbeitet einen einzelnen RawArticle: Ruft den relevanten Text ab und fasst ihn zusammen.
        Gibt ein ProcessedArticle-Objekt zurück.
        """
        if self.llm is None: # Prüfung aus BaseLLMProcessor
             logger.error("LLM nicht initialisiert im SummarizerAgent. Verarbeitung für Artikel abgebrochen.")
             # Erstelle ein ProcessedArticle mit einer Fehlermeldung in der Zusammenfassung
             return ProcessedArticle(
                 title=article.title or "Unbekannter Titel",
                 url=article.url,
                 summary="Fehler: LLM nicht verfügbar für Zusammenfassung.",
                 source_name=article.source_name,
                 published_at=article.published_at
             )
             
        text_to_summarize = self._get_text_for_summarization(article)
        summary = self.summarize_article_text(article.title, text_to_summarize)
        
        return ProcessedArticle(
            title=article.title or "Unbekannter Titel",
            url=article.url,
            summary=summary,
            # Kategorie und Relevanz werden von anderen Agenten hinzugefügt
            source_name=article.source_name,
            published_at=article.published_at,
            llm_processing_details={"summarizer_model": self.model_name}
        )

    def process_batch(self, articles: List[RawArticle]) -> List[ProcessedArticle]:
        """
        Verarbeitet eine Liste von RawArticle-Objekten und gibt eine Liste von ProcessedArticle-Objekten
        mit den generierten Zusammenfassungen zurück. (Dies ist die umbenannte `process`-Methode)
        """
        if self.llm is None:
             logger.error("LLM nicht initialisiert im SummarizerAgent. Batch-Verarbeitung abgebrochen.")
             return []
             
        logger.info(f"Starte Batch-Zusammenfassung für {len(articles)} Artikel...")
        processed_articles_list: List[ProcessedArticle] = []
        
        for i, article_item in enumerate(articles):
            logger.debug(f"Verarbeite Artikel {i+1}/{len(articles)} im Batch: '{article_item.title}'")
            processed_articles_list.append(self.process_article(article_item))
            
        logger.info(f"Batch-Zusammenfassung für {len(processed_articles_list)} Artikel abgeschlossen.")
        return processed_articles_list
