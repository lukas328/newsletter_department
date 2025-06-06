from src.orchestrator import NewsletterOrchestrator
from src.models.data_models import RawArticle


def test_filter_blacklisted_sources():
    orch = object.__new__(NewsletterOrchestrator)
    orch.source_blacklist = ["badsource"]

    articles = [
        RawArticle(title="a", source_name="Good", source_id="good"),
        RawArticle(title="b", source_name="BadSource", source_id="badsource"),
        RawArticle(title="c", source_name="Another", source_id="other"),
    ]
    filtered = orch._filter_blacklisted_sources(articles)
    assert len(filtered) == 2
    assert all(a.source_id != "badsource" for a in filtered)
