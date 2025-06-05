# newsletter_project/src/models/data_models.py
# Pydantic-Modelle zur Definition der Datenstrukturen.

from pydantic import BaseModel, HttpUrl, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date, timezone
import logging

logger = logging.getLogger(__name__)

def ensure_timezone_aware(dt_value: Optional[Union[datetime, str]]) -> Optional[datetime]:
    """Stellt sicher, dass ein datetime-Objekt timezone-aware ist (UTC als Default). Akzeptiert auch Strings."""
    if dt_value is None:
        return None
    
    if isinstance(dt_value, str):
        try:
            # Versuche, gängige ISO-Formate zu parsen, inklusive 'Z' für UTC
            if dt_value.endswith('Z'):
                dt_value = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            else:
                # Prüfe, ob bereits Zeitzoneninfo vorhanden ist
                # Dieser Teil ist etwas heikel, da fromisoformat nicht alle TZ-Formate direkt mag
                try:
                    dt_value = datetime.fromisoformat(dt_value)
                except ValueError: # Fallback für Formate wie "YYYY-MM-DD HH:MM:SS" ohne TZ
                    dt_value = datetime.strptime(dt_value, "%Y-%m-%d %H:%M:%S")

        except ValueError as e:
            logger.warning(f"Ungültiges Datumsstring-Format für Konvertierung: '{dt_value}'. Fehler: {e}")
            return None # Oder wirf einen Fehler, je nach gewünschtem Verhalten

    if not isinstance(dt_value, datetime): # Wenn nach der Konvertierung immer noch kein datetime
        logger.warning(f"Wert '{dt_value}' konnte nicht in ein datetime-Objekt konvertiert werden.")
        return None

    if dt_value.tzinfo is None or dt_value.tzinfo.utcoffset(dt_value) is None:
        # Wenn keine Zeitzoneninfo vorhanden ist, setze auf UTC
        return dt_value.replace(tzinfo=timezone.utc)
    # Wenn bereits timezone-aware, gib es direkt zurück
    return dt_value

class RawArticle(BaseModel):
    title: Optional[str] = Field(default=None)
    url: Optional[HttpUrl] = Field(default=None)
    description: Optional[str] = Field(default=None)
    content_snippet: Optional[str] = Field(default=None) 
    published_at: Optional[datetime] = Field(default=None)
    source_name: Optional[str] = Field(default=None)
    source_id: Optional[str] = Field(default=None) # z.B. von NewsAPI

    _ensure_published_at_tz_aware = field_validator('published_at', mode='before')(ensure_timezone_aware)

class ProcessedArticle(BaseModel):
    title: str
    url: Optional[HttpUrl] = Field(default=None)
    summary: str
    category: Optional[str] = Field(default="Unkategorisiert")
    relevance_score: Optional[float] = Field(default=0.0, ge=0.0, le=1.0) 
    source_name: Optional[str] = Field(default=None)
    published_at: Optional[datetime] = Field(default=None)
    llm_processing_details: Dict[str, Any] = Field(default_factory=dict)
    article_text: Optional[str] = Field(default=None)

    _ensure_published_at_tz_aware = field_validator('published_at', mode='before')(ensure_timezone_aware)

class Event(BaseModel):
    summary: str # Titel des Events
    start_time: Optional[datetime] = Field(default=None)
    end_time: Optional[datetime] = Field(default=None)
    location: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None)
    url: Optional[HttpUrl] = Field(default=None)
    source: str # z.B. "Google Calendar", "Veranstaltungen Zürich API"

    _ensure_start_time_tz_aware = field_validator('start_time', mode='before')(ensure_timezone_aware)
    _ensure_end_time_tz_aware = field_validator('end_time', mode='before')(ensure_timezone_aware)

class Birthday(BaseModel):
    name: str
    date_month: int = Field(ge=1, le=12)
    date_day: int = Field(ge=1, le=31)
    original_date_info: Optional[str] = Field(default=None) 
    source: str 

class WeatherInfo(BaseModel):
    location: str
    temperature_celsius: float
    condition: str 
    humidity_percent: Optional[float] = Field(default=None)
    wind_speed_kmh: Optional[float] = Field(default=None)
    icon_url: Optional[HttpUrl] = Field(default=None) 
    forecast_snippet: Optional[str] = Field(default=None) 

class NewsletterSection(BaseModel):
    title: str 
    items: List[Union[ProcessedArticle, Event, Birthday, WeatherInfo, Dict[str, Any]]] # Erlaube verschiedene Typen

class NewsletterData(BaseModel):
    generation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    title: str = Field(default="Dein personalisierter Newsletter")
    sections: List[NewsletterSection]

    _ensure_generation_date_tz_aware = field_validator('generation_date', mode='before')(ensure_timezone_aware)
