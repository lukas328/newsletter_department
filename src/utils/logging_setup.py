# newsletter_project/src/utils/logging_setup.py
# Konfiguriert das zentrale Logging für die Anwendung.

import logging
import sys
import os
from typing import Optional

# Basiskonfiguration, falls setup_logging nicht explizit aufgerufen wird oder früh geloggt wird
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def setup_logging(log_level_str: str = "INFO", log_file: Optional[str] = None):
    """
    Konfiguriert das Logging-System für die gesamte Anwendung.
    Diese Funktion sollte möglichst früh im Anwendungslauf aufgerufen werden (z.B. in main.py).

    Args:
        log_level_str (str): Logging-Level als String (z.B. "DEBUG", "INFO", "WARNING").
        log_file (Optional[str]): Optionaler Pfad zu einer Log-Datei. 
                                   Wenn None, wird nur auf der Konsole geloggt.
    """
    # Hole den Root-Logger, um die Konfiguration global anzuwenden.
    root_logger = logging.getLogger()

    # Bestimme das numerische Log-Level
    # Hole Default Log-Level aus Umgebungsvariable LOG_LEVEL, falls vorhanden, sonst nimm Parameter.
    # Dies erlaubt Überschreiben des Levels via .env ohne Codeänderung.
    effective_log_level_str = os.getenv("LOG_LEVEL", log_level_str).upper()
    numeric_level = getattr(logging, effective_log_level_str, None)
    
    if not isinstance(numeric_level, int):
        # Nutze print, da Logging hier ggf. noch nicht voll initialisiert ist für Fehlermeldungen
        print(f"WARNUNG: Ungültiger Log-Level '{effective_log_level_str}' (aus Umgebung oder Default). Verwende INFO als Fallback.", file=sys.stderr)
        numeric_level = logging.INFO

    # Setze das Level für den Root-Logger.
    root_logger.setLevel(numeric_level)

    # Definiere das Format für Log-Nachrichten
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Entferne ggf. vorhandene Handler, um Doppel-Logging zu vermeiden,
    # besonders wenn diese Funktion mehrmals aufgerufen werden könnte oder von
    # externen Bibliotheken bereits Handler gesetzt wurden.
    # Sei vorsichtig hiermit, wenn du das Logging von Third-Party-Libs behalten willst.
    # Eine Alternative ist, nur Handler hinzuzufügen, wenn keine existieren oder spezifische Handler zu managen.
    # Für eine saubere Konfiguration ist es oft am besten, vorhandene zu entfernen.
    if root_logger.hasHandlers():
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

    # Konsolen-Handler konfigurieren und hinzufügen
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    # Das Level des Handlers kann feingranularer sein, aber meistens ist es gleich dem Root-Level.
    console_handler.setLevel(numeric_level) 
    root_logger.addHandler(console_handler)

    # Datei-Handler konfigurieren und hinzufügen, falls ein Dateipfad angegeben wurde
    # Hole Log-Datei-Pfad aus Umgebungsvariable LOG_FILE, falls vorhanden, überschreibe Parameter.
    effective_log_file = os.getenv("LOG_FILE", log_file)
    if effective_log_file:
        try:
            log_dir = os.path.dirname(effective_log_file)
            if log_dir and not os.path.exists(log_dir): # Erstelle Verzeichnis, falls nicht vorhanden
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(effective_log_file, mode='a', encoding='utf-8') # 'a' für append
            file_handler.setFormatter(formatter)
            file_handler.setLevel(numeric_level) # Setze Level auch für den Datei-Handler
            root_logger.addHandler(file_handler)
            logging.info(f"Logging zusätzlich in Datei konfiguriert: {os.path.abspath(effective_log_file)}")
        except Exception as e:
            # Nutze print, da Logging hier ggf. noch nicht voll initialisiert ist für Fehlermeldungen
            print(f"FEHLER: Konnte Datei-Log-Handler für '{effective_log_file}' nicht erstellen: {e}", file=sys.stderr)
    
    # Eine erste Log-Nachricht, um zu signalisieren, dass das Logging (neu) konfiguriert wurde.
    # Dies wird mit dem neu konfigurierten Logger ausgegeben.
    logging.info(f"Logging-System initialisiert/rekonfiguriert. Effektives Level: {logging.getLevelName(root_logger.getEffectiveLevel())}.")
