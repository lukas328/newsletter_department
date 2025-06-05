from src.utils.epub_utils import generate_epub
from src.models.data_models import ProcessedArticle


def test_generate_epub(tmp_path):
    articles = [
        ProcessedArticle(title="A", summary="Sum A"),
        ProcessedArticle(title="B", summary="Sum B"),
    ]
    out_file = tmp_path / "test.epub"
    generate_epub(
        articles,
        str(out_file),
        articles_per_page=2,
        use_a4_css=True,
        quote_of_the_day="Testquote",
        quote_author="Tester",
    )
    assert out_file.exists()

