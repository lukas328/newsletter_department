# newsletter_project/src/utils/config_loader.py
# Lädt Umgebungsvariablen und stellt Konfigurationen bereit.

import os
from dotenv import load_dotenv
import logging
from typing import Optional

logger = logging.getLogger(__name__) # Logger für dieses Modul

def load_env():
    """
    Lädt Umgebungsvariablen aus einer .env Datei im Projektwurzelverzeichnis.
    Das Projektwurzelverzeichnis wird angenommen als ein Level über dem 'src' Verzeichnis.
    """
    # Gehe zum Projektwurzelverzeichnis, um .env zu finden
    # Annahme: Dieses Skript ist in src/utils/
    current_dir = os.path.dirname(os.path.abspath(__file__)) # Gibt /pfad/zum/projekt/src/utils
    src_dir = os.path.dirname(current_dir) # Gibt /pfad/zum/projekt/src
    project_root = os.path.dirname(src_dir) # Gibt /pfad/zum/projekt
    dotenv_path = os.path.join(project_root, '.env')
    
    if os.path.exists(dotenv_path):
        loaded = load_dotenv(dotenv_path)
        if loaded:
            logger.info(f".env Datei erfolgreich geladen von: {dotenv_path}")
        else:
            logger.warning(f"Konnte .env Datei nicht laden von: {dotenv_path}, obwohl sie existiert. Prüfe Dateirechte oder Inhalt.")
    else:
        # Dies ist kein Fehler, da Umgebungsvariablen auch anders gesetzt sein können (z.B. im System oder Docker).
        logger.info(f".env Datei nicht gefunden unter: {dotenv_path}. Umgebungsvariablen müssen anderweitig gesetzt sein für produktiven Betrieb.")

def get_env_variable(variable_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Holt eine Umgebungsvariable. Gibt den Defaultwert zurück, falls nicht gefunden.
    Loggt eine Warnung, wenn die Variable nicht gefunden wird und kein Defaultwert angegeben ist.
    """
    value = os.getenv(variable_name, default)
    if value is None and default is None: 
        # Logge als Debug, da dies oft erwartet wird (z.B. für optionale Einstellungen)
        logger.debug(f"Umgebungsvariable '{variable_name}' nicht gefunden und kein Defaultwert angegeben.")
    elif value is default and default is not None and os.getenv(variable_name) is None:
        logger.debug(f"Umgebungsvariable '{variable_name}' nicht gefunden, verwende Defaultwert: '{default}'.")
    return value

def get_api_key(key_name: str) -> str:
    """
    Holt einen API-Schlüssel. Löst einen ValueError aus und loggt kritisch, wenn nicht gefunden.
    """
    api_key = os.getenv(key_name)
    if not api_key:
        logger.critical(f"Kritischer Fehler: API-Schlüssel '{key_name}' nicht in den Umgebungsvariablen gefunden.")
        raise ValueError(f"API-Schlüssel '{key_name}' nicht in den Umgebungsvariablen gefunden. Bitte in .env setzen oder als System-Umgebungsvariable definieren.")
    logger.debug(f"API-Schlüssel '{key_name}' erfolgreich geladen.")
    return api_key
