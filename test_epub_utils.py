from src.utils.epub_utils import generate_epub
from src.models.data_models import ProcessedArticle, WeatherInfo


def test_generate_epub(tmp_path):
    articles = [
        ProcessedArticle(title="A", summary="Sum A"),
        ProcessedArticle(title="B", summary="Sum B"),
    ]
    out_file = tmp_path / "test.epub"
    weather = [WeatherInfo(location="Zurich", temperature_celsius=20.0, condition="sonnig", forecast_snippet="Tag 1: 20°C sonnig")]
    generate_epub(articles, str(out_file), articles_per_page=2, use_a4_css=True, weather_infos=weather)
    assert out_file.exists()

