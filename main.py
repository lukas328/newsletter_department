# newsletter_project/main.py
# Haupt-Einstiegspunkt zum Starten der Newsletter-Pipeline.

# Importiere den Orchestrator erst, wenn er existiert und benötigt wird.
# from src.orchestrator import NewsletterOrchestrator 
from src.utils.logging_setup import setup_logging
from src.utils.config_loader import load_env, get_env_variable
import logging

if __name__ == "__main__":
    # Lade Umgebungsvariablen ganz am Anfang
    load_env()

    # Konfiguriere Logging frühzeitig
    # Hole LOG_LEVEL und LOG_FILE aus .env, mit Defaults
    log_level = get_env_variable("LOG_LEVEL", "INFO")
    log_file_path = get_env_variable("LOG_FILE") # Kann None sein, dann nur Konsole
    setup_logging(log_level_str=log_level, log_file=log_file_path)

    logger = logging.getLogger(__name__) # Logger für main.py

    logger.info("Starte den Newsletter-Generierungsprozess (main.py)...")
    
    #--- Platzhalter für den Orchestrator-Aufruf ---
    try:
        from src.orchestrator import NewsletterOrchestrator # Import hier, um zirkuläre Abhängigkeiten zu vermeiden
        orchestrator = NewsletterOrchestrator() 
        result = orchestrator.run_pipeline()
        
        if result:
            logger.info(f"Newsletter-Pipeline erfolgreich abgeschlossen. Ergebnis: {result}")
        else:
            logger.warning("Newsletter-Pipeline abgeschlossen, aber kein Ergebnis zurückgegeben.")
    except ImportError:
       logger.error("Orchestrator konnte nicht importiert werden. Stelle sicher, dass src.orchestrator.py existiert.")
    except Exception as e:
        logger.critical(f"Ein kritischer Fehler ist in main.py aufgetreten: {e}", exc_info=True)
    
    logger.info("Platzhalter: Pipeline-Logik würde hier folgen.")
    # --- Ende Platzhalter ---

    logger.info("Newsletter-Generierungsprozess (main.py) beendet (oder wäre hier beendet).")