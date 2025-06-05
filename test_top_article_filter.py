from src.orchestrator import NewsletterOrchestrator
from src.models.data_models import RawArticle, ProcessedArticle

class DummySummarizer:
    def process_batch(self, raws):
        return [
            ProcessedArticle(title=r.title or "", summary="sum", url=r.url, source_name=r.source_name, published_at=r.published_at)
            for r in raws
        ]

class DummyCategorizer:
    def __init__(self, scores):
        self.scores = scores

    def process_batch(self, arts):
        for art, score in zip(arts, self.scores):
            art.category = "Dummy"
            art.relevance_score = score
        return arts

class DummyWriter:
    def __init__(self):
        self.received = []
        self.model_name = "dummy"

    def process_batch(self, arts):
        self.received = arts
        return [f"text{idx}" for idx, _ in enumerate(arts)]

def test_only_top_articles_written():
    orch = object.__new__(NewsletterOrchestrator)
    orch.summarizer = DummySummarizer()
    orch.categorizer = DummyCategorizer([9, 2, 8])
    orch.article_writer = DummyWriter()
    orch.top_article_count = 2

    raws = [RawArticle(title=f"T{i}") for i in range(3)]
    processed = orch._process_articles_with_llm(raws)

    assert len(orch.article_writer.received) == 2
    titles = [a.title for a in orch.article_writer.received]
    assert titles == ["T0", "T2"]

    assert processed[0].article_text is not None
    assert processed[2].article_text is not None
    assert processed[1].article_text is None
