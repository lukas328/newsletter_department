# newsletter_project/src/agents/llm_processors/categorizer_agent.py
# LLM-Agent zum Kategorisieren von Texten (z.B. Artikel).

from typing import List, Optional, Union, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser 
from langchain_core.pydantic_v1 import BaseModel as LangchainBaseModel, Field as LangchainField
from src.models.data_models import ProcessedArticle # Arbeitet jetzt mit ProcessedArticle (hat schon summary)
from .base_processor import BaseLLMProcessor
import logging
import json # Für manuelles Parsen, falls JsonOutputParser nicht perfekt funktioniert

logger = logging.getLogger(__name__)

# Pydantic-Modell für die erwartete JSON-Ausgabe der Kategorisierung
# Dieses Modell wird vom JsonOutputParser verwendet, um die LLM-Antwort zu validieren und zu parsen.
class CategorizationResponseSchema(LangchainBaseModel):
    category: str = LangchainField(description="Die am besten passende Kategorie für den Artikel aus der vorgegebenen Liste.")
    importance: int = LangchainField(description="Wichtigkeit des Artikels für das Thema auf einer Skala von 1 bis 10.")
    # Optional: confidence und reasoning können für detaillierteres Feedback hinzugefügt werden.
    # confidence: Optional[float] = LangchainField(description="Konfidenzwert der Kategorisierung (0.0 bis 1.0).", default=None)
    # reasoning: Optional[str] = LangchainField(description="Kurze Begründung für die gewählte Kategorie.", default=None)


class CategorizerAgent(BaseLLMProcessor):
    """
    Ein LLM-Agent, der darauf spezialisiert ist, Artikel
    in vordefinierte Kategorien einzuordnen.
    """
    def __init__(self, 
                 categories: List[str], # Die Liste der erlaubten Kategorien
                 model_name: Optional[str] = None,
                 temperature: float = 1): # Sehr niedrige Temperatur für konsistente Kategorisierung
        super().__init__(model_name=model_name, temperature=temperature)
        
        if not categories:
            logger.error("CategorizerAgent erfordert eine Liste von Kategorien bei der Initialisierung.")
            raise ValueError("Es müssen Kategorien für den CategorizerAgent bereitgestellt werden.")
        self.categories_list = categories # Speichere als Liste für die Validierung der LLM-Antwort
        self.categories_str = ", ".join(f"'{cat}'" for cat in categories) # Format für den Prompt

        # Definiere das Prompt-Template für die Kategorisierung
        self.prompt_template = ChatPromptTemplate.from_template( # Vereinfacht zu from_template für Klarheit
             """
Du bist ein Experte für die thematische Kategorisierung von Nachrichtenartikeln.
Deine Aufgabe ist es, den folgenden Artikel EINER der vorgegebenen Kategorien zuzuordnen.
Antworte ausschließlich im JSON-Format. Das JSON-Objekt muss einen Schlüssel "category" enthalten, 
dessen Wert eine der unten genannten Kategorien sein muss.

Vorgegebene Kategorien: [{available_categories}]

Wähle nur eine einzige, die absolut relevanteste Kategorie aus der Liste.
Wenn keine Kategorie exakt passt, wähle die allgemeinste passende Kategorie aus der Liste oder, falls vorhanden, eine Kategorie wie 'Sonstiges' oder 'Der Rund um Blick'.
Gib KEINEN zusätzlichen Text oder Erklärungen außerhalb des JSON-Objekts zurück.

Bewerte außerdem, wie wichtig dieser Artikel im Kontext des Themas ist. Verwende eine Skala von 1 (sehr unwichtig) bis 10 (sehr wichtig) und gib die Zahl im Feld "importance" zurück.

ARTIKELTITEL: {title}
ARTIKELZUSAMMENFASSUNG: {summary}

JSON-ANTWORT (nur das JSON-Objekt):
"""
        )
        
        # Erstelle die LangChain-Kette mit einem JSON-Output-Parser
        self.output_parser = JsonOutputParser(pydantic_object=CategorizationResponseSchema)
        
        self.chain = self.prompt_template | self.llm | self.output_parser
        logger.info(f"CategorizerAgent Kette initialisiert mit Kategorien: {self.categories_str}.")

    def _get_text_for_categorization(self, article: ProcessedArticle) -> str:
        """Kombiniert Titel und Zusammenfassung für die Kategorisierung."""
        title = article.title or ""
        summary = article.summary or ""
        # Kombiniere Titel und Zusammenfassung für besseren Kontext, falls beides vorhanden
        if title and summary:
            return f"Titel: {title}\nZusammenfassung: {summary}"
        elif summary:
            return summary
        elif title:
            return title
        return ""

    def categorize_article(self, article: ProcessedArticle) -> str:
        """
        Kategorisiert einen einzelnen ProcessedArticle.
        Gibt den Namen der Kategorie als String zurück.
        """
        logger.debug(f"Kategorisierung für Artikel angefordert: '{article.title}'")
        
        text_to_categorize = self._get_text_for_categorization(article)
        
        if not text_to_categorize or len(text_to_categorize.strip()) < 10: # Mindestlänge für sinnvollen Input
            logger.warning(f"Kein ausreichender Inhalt (Titel/Zusammenfassung) zum Kategorisieren für Artikel: '{article.title}'")
            return "Unkategorisiert" # Standardkategorie bei unzureichendem Input

        try:
            # Begrenze die Länge des Inputs für den LLM, falls nötig
            max_input_chars = 2500 # Titel + Zusammenfassung sollten hier reinpassen
            
            # Das Ergebnis des JsonOutputParser(pydantic_object=...) ist bereits ein Dictionary
            # (oder das Pydantic-Objekt selbst, wenn man es direkt verwenden würde)
            response_data: Dict = self.chain.invoke({
                "available_categories": self.categories_str,
                "title": article.title or "Kein Titel", # Stelle sicher, dass immer ein Titel da ist
                "summary": article.summary[:max_input_chars] # Nur Zusammenfassung als Haupttext
            })
            
            category = response_data.get("category", "Unkategorisiert")
            importance_val = response_data.get("importance", 0)

            try:
                importance_score = float(importance_val)
            except (TypeError, ValueError):
                importance_score = 0.0

            if importance_score < 0 or importance_score > 10:
                logger.warning(
                    f"Erhaltene Wichtigkeit '{importance_score}' außerhalb des erwarteten Bereichs 1-10 für Artikel '{article.title}'."
                )
                importance_score = max(0.0, min(importance_score, 10.0))

            article.relevance_score = importance_score
            if article.llm_processing_details is None:
                article.llm_processing_details = {}
            article.llm_processing_details["importance"] = importance_score

            # Zusätzliche Validierung: Stelle sicher, dass die zurückgegebene Kategorie eine der erlaubten ist.
            # Manchmal halluzinieren LLMs Kategorien, die nicht in der Liste standen.
            if category not in self.categories_list and category != "Unkategorisiert" and category != "Fehler bei Kategorisierung":
                logger.warning(f"LLM gab eine ungültige Kategorie '{category}' zurück für Artikel '{article.title}' (nicht in der Liste: {self.categories_list}). Setze auf 'Unkategorisiert'.")
                category = "Unkategorisiert"

            logger.debug(f"Artikel '{article.title}' kategorisiert als: '{category}'.")
            return category

        except json.JSONDecodeError as e_json: # Falls der LLM kein valides JSON liefert trotz Anweisung
            logger.error(f"Fehler beim Parsen der JSON-Kategorisierungsantwort für '{article.title}': {e_json}. Überprüfe den LLM-Output.", exc_info=True)
            return "Fehler bei Kategorisierung (JSON)"
        except Exception as e:
            logger.error(f"Fehler beim Kategorisieren des Artikels '{article.title}': {e}", exc_info=True)
            return "Fehler bei Kategorisierung (Allgemein)" # Fallback

    def process_batch(self, processed_articles: List[ProcessedArticle]) -> List[ProcessedArticle]:
        """
        Verarbeitet eine Liste von ProcessedArticle-Objekten und fügt jedem die Kategorie hinzu.
        Gibt die modifizierte Liste zurück.
        """
        if self.llm is None:
             logger.error("LLM nicht initialisiert im CategorizerAgent. Batch-Verarbeitung abgebrochen.")
             return processed_articles # Gib die Liste unverändert zurück oder eine leere Liste
             
        logger.info(f"Starte Batch-Kategorisierung für {len(processed_articles)} Artikel.")
        
        for i, article in enumerate(processed_articles):
            logger.debug(f"Kategorisiere Artikel {i+1}/{len(processed_articles)} im Batch: '{article.title}'")
            category_name = self.categorize_article(article)
            article.category = category_name # Aktualisiere das ProcessedArticle-Objekt direkt
            if article.llm_processing_details is None: article.llm_processing_details = {}
            article.llm_processing_details["categorizer_model"] = self.model_name
            article.llm_processing_details["assigned_category"] = category_name
            
        logger.info(f"Batch-Kategorisierung für {len(processed_articles)} Artikel abgeschlossen.")
        return processed_articles
