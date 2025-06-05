# newsletter_project/src/agents/llm_processors/base_processor.py
# Abstrakte Basisklasse für alle LLM-basierten Verarbeitungs-Agenten.

from abc import ABC, abstractmethod
from typing import Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI # Für Gemini
from langchain_core.language_models.chat_models import BaseChatModel # Basistyp für ChatModelle
from src.utils.config_loader import get_api_key, get_env_variable # Für API-Key und Modellnamen
import logging

logger = logging.getLogger(__name__)

class BaseLLMProcessor(ABC):
    """
    Abstrakte Basisklasse für Agenten, die Daten mithilfe eines LLM verarbeiten.
    Verwendet standardmäßig Google Gemini via LangChain.
    """
    def __init__(self, 
                 model_name: Optional[str] = None, 
                 temperature: float = 0.3, # Standardtemperatur für ausgewogene Kreativität
                 llm_provider: str = "gemini"): # Könnte erweitert werden für "openai" etc.
        """
        Initialisiert den LLM-Prozessor.
        Args:
            model_name (str, optional): Der Name des zu verwendenden LLM-Modells. 
                                        Wird aus .env (GEMINI_DEFAULT_MODEL) geholt, falls nicht angegeben.
            temperature (float): Die Temperatur für die LLM-Generierung.
            llm_provider (str): Der Anbieter des LLM (derzeit nur "gemini" implementiert).
        """
        self.llm_provider = llm_provider.lower()
        self.model_name = model_name
        self.temperature = temperature
        self.llm: Optional[BaseChatModel] = None # Der LangChain LLM-Client

        logger.info(f"Initialisiere LLM Processor für Provider: '{self.llm_provider}'.")

        try:
            if self.llm_provider == "gemini":
                gemini_api_key = get_api_key("GOOGLE_API_KEY") # Stellt sicher, dass der Key existiert
                
                # Hole Default-Modellnamen aus .env, falls nicht explizit übergeben
                default_gemini_model = get_env_variable("GEMINI_DEFAULT_MODEL", "gemini-1.5-flash-latest")
                self.model_name = model_name if model_name else default_gemini_model
                
                self.llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=gemini_api_key,
                    temperature=self.temperature,
                    # convert_system_message_to_human=True # Kann nützlich sein, je nach Prompt-Struktur
                                                        # LangChain's ChatPromptTemplate handhabt Rollen aber gut.
                )
                logger.info(f"Gemini LLM Processor initialisiert mit Modell: {self.model_name}, Temperatur: {self.temperature}.")
            # Hier könnte man andere Provider wie OpenAI hinzufügen
            # elif self.llm_provider == "openai":
            #     # ... Implementierung für OpenAI ...
            else:
                logger.error(f"Nicht unterstützter LLM-Provider: {self.llm_provider}")
                raise ValueError(f"Nicht unterstützter LLM-Provider: {self.llm_provider}")
        except Exception as e:
            logger.critical(f"Fehler bei der Initialisierung des LLM-Clients für Provider '{self.llm_provider}' mit Modell '{self.model_name}': {e}", exc_info=True)
            # Optional: Workflow hier abbrechen oder einen Fallback-Mechanismus implementieren
            raise # Fehler weiterwerfen, um das Problem im Orchestrator sichtbar zu machen

    @abstractmethod
    def process(self, data: Any, **kwargs) -> Any:
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
