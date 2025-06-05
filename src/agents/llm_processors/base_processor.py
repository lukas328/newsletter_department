# newsletter_project/src/agents/llm_processors/base_processor.py
# Abstrakte Basisklasse für alle LLM-basierten Verarbeitungs-Agenten.

from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel # Basistyp für ChatModelle
from src.utils.config_loader import get_api_key, get_env_variable # Für API-Key und Modellnamen
import logging

logger = logging.getLogger(__name__)

class BaseLLMProcessor(ABC):
    """
    Abstrakte Basisklasse für Agenten, die Daten mithilfe eines LLM verarbeiten.
    Standardmäßig wird OpenAI GPT über LangChain verwendet.
    """
    def __init__(self, 
                 model_name: Optional[str] = None, 
                 temperature: float = 0.3, # Standardtemperatur für ausgewogene Kreativität
                 llm_provider: str = "openai"):
        """
        Initialisiert den LLM-Prozessor.
        Args:
            model_name (str, optional): Der Name des zu verwendenden LLM-Modells.
                                        Wird aus .env (OPENAI_DEFAULT_MODEL) geholt, falls nicht angegeben.
            temperature (float): Die Temperatur für die LLM-Generierung.
            llm_provider (str): Der Anbieter des LLM (derzeit "openai" oder "gpt").
        """
        self.llm_provider = llm_provider.lower()
        self.model_name = model_name
        self.temperature = temperature
        self.llm: Optional[BaseChatModel] = None # Der LangChain LLM-Client

        logger.info(f"Initialisiere LLM Processor für Provider: '{self.llm_provider}'.")

        try:
            if self.llm_provider in ["openai", "gpt"]:
                openai_api_key = get_api_key("OPENAI_API_KEY")
                default_model = get_env_variable("OPENAI_DEFAULT_MODEL", "gpt-3.5-turbo")
                self.model_name = model_name if model_name else default_model

                self.llm = ChatOpenAI(
                    model=self.model_name,
                    openai_api_key=openai_api_key,
                    temperature=self.temperature,
                )
                logger.info(
                    f"OpenAI LLM Processor initialisiert mit Modell: {self.model_name}, Temperatur: {self.temperature}."
                )
            else:
                logger.error(f"Nicht unterstützter LLM-Provider: {self.llm_provider}")
                raise ValueError(f"Nicht unterstützter LLM-Provider: {self.llm_provider}")
        except Exception as e:
            logger.critical(f"Fehler bei der Initialisierung des LLM-Clients für Provider '{self.llm_provider}' mit Modell '{self.model_name}': {e}", exc_info=True)
            # Optional: Workflow hier abbrechen oder einen Fallback-Mechanismus implementieren
            raise # Fehler weiterwerfen, um das Problem im Orchestrator sichtbar zu machen

    @abstractmethod
    def process_batch(self, data: Any, **kwargs) -> Any:
        """
        Abstrakte Methode zur Verarbeitung der Eingabedaten mit dem LLM.
        Muss von abgeleiteten Klassen implementiert werden.

        Args:
            data (Any): Die zu verarbeitenden Eingabedaten.
            **kwargs: Zusätzliche Argumente für den Verarbeitungsprozess.

        Returns:
            Any: Die verarbeiteten Daten.
        """
        if self.llm is None:
            logger.error("LLM wurde nicht korrekt initialisiert. Verarbeitung nicht möglich.")
            raise RuntimeError("LLM nicht initialisiert. Verarbeitung abgebrochen.")
        pass # Implementierung in abgeleiteten Klassen

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(model='{self.model_name}', provider='{self.llm_provider}')>"
