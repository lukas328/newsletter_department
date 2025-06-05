from src.utils.epub_utils import generate_epub
from src.models.data_models import ProcessedArticle, Event


def test_generate_epub(tmp_path):
    articles = [
        ProcessedArticle(title="A", summary="Sum A"),
        ProcessedArticle(title="B", summary="Sum B"),
    ]
    events = [
        Event(summary="Meeting", start_time="2025-01-01T10:00:00Z", source="Google Calendar"),
    ]
    out_file = tmp_path / "test.epub"
    generate_epub(articles, str(out_file), articles_per_page=2, use_a4_css=True, events=events)
    assert out_file.exists()

