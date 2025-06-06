from src.utils.epub_utils import generate_epub

from src.models.data_models import ProcessedArticle, Event,TodoItem, WeatherInfo
import zipfile



def test_generate_epub(tmp_path):
    articles = [
        ProcessedArticle(title="A", summary="Sum A"),
        ProcessedArticle(title="B", summary="Sum B"),
    ]

    out_file = tmp_path / "test.epub"
    generate_epub(articles, str(out_file), articles_per_page=2, use_a4_css=True,)


    weather = [WeatherInfo(location="Zurich", temperature_celsius=20.0, condition="sonnig", forecast_snippet="Tag 1: 20°C sonnig")]
    events = []
    generate_epub(
        articles,
        str(out_file),
        articles_per_page=2,
        use_a4_css=True,
        quote_of_the_day="Testquote",
        quote_author="Tester",
        weather_infos=weather,
        events=events,
    )


    assert out_file.exists()


def test_generate_epub_with_todos(tmp_path):
    articles = [ProcessedArticle(title="A", summary="Sum A")]
    todos = [TodoItem(id=1, content="Aufgabe 1"), TodoItem(id=2, content="Aufgabe 2")]
    out_file = tmp_path / "todos.epub"
    generate_epub(articles, str(out_file), todos=todos)
    assert out_file.exists()
    with zipfile.ZipFile(out_file, "r") as zf:
        names = zf.namelist()
        todo_file = [n for n in names if "chap_todos.xhtml" in n][0]
        data = zf.read(todo_file).decode("utf-8")
        assert "Aufgabe 1" in data


