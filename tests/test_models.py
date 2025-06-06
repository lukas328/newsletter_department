# test_models.py (im Hauptverzeichnis oder einem separaten 'tests'-Ordner)
from src.models.data_models import RawArticle, ProcessedArticle, NewsletterData, NewsletterSection
from datetime import datetime

# Lade .env Variablen, damit Logging etc. ggf. schon konfiguriert ist
# (obwohl für reinen Modelltest nicht zwingend nötig)
# from src.utils.config_loader import load_env
# load_env()

try:
    # Test RawArticle
    raw1 = RawArticle(title="Test News", url="http://example.com", published_at="2025-06-04T10:00:00Z")
    print(f"Raw Article: {raw1.title}, Published: {raw1.published_at} (TZ: {raw1.published_at.tzinfo})")

    raw2 = RawArticle(title="Kein Datum")
    print(f"Raw Article 2: {raw2.title}, Published: {raw2.published_at}")

    raw3 = RawArticle(title="String Datum ohne TZ", published_at="2025-06-04 12:30:00")
    print(f"Raw Article 3: {raw3.title}, Published: {raw3.published_at} (TZ: {raw3.published_at.tzinfo})")

    # Test ProcessedArticle
    proc1 = ProcessedArticle(title="Verarbeiteter Artikel", summary="Dies ist eine tolle Zusammenfassung.", category="IT & AI")
    print(f"Processed Article: {proc1.title}, Category: {proc1.category}, Score: {proc1.relevance_score}")

    # Test NewsletterData
    section1 = NewsletterSection(title="Top News", items=[proc1])
    newsletter = NewsletterData(sections=[section1])
    print(f"Newsletter Titel: {newsletter.title}, Generiert am: {newsletter.generation_date}")
    print(f"Erste Sektion: {newsletter.sections[0].title}, Enthält: {len(newsletter.sections[0].items)} Artikel")

    print("\nDatenmodell-Tests erfolgreich (grundlegend).")

except Exception as e:
    print(f"\nFehler beim Testen der Datenmodelle: {e}")
