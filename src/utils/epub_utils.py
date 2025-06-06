from ebooklib import epub

from typing import List, Optional, Tuple

from src.models.data_models import (
    Event,
    ProcessedArticle,
    TodoItem,
    WeatherInfo,
)




def _build_a4_style() -> str:
    """Return a simple CSS style for A4 sized pages."""
    return (
        "@page { size: A4; margin: 2cm; }"
        "body { font-family: serif; }"
        "h1 { font-size: 1.4em; margin-bottom: 0.2em; }"
        "p { margin-top: 0; margin-bottom: 0.5em; }"
    )


def generate_epub(
    articles: List[ProcessedArticle],
    output_path: str,
    articles_per_page: int = 1,
    use_a4_css: bool = False,

    extra_chapters: Optional[List[Tuple[str, str]]] = None,

    events: Optional[List[Event]] = None,
    todos: Optional[List[TodoItem]] = None,
    weather_infos: Optional[List[WeatherInfo]] = None,
    quote_of_the_day: str | None = None,
    quote_author: str | None = None,

) -> str:
    """Generiert eine EPUB-Datei aus Artikeln.

    Args:
        articles: Die zu verarbeitenden Artikel.
        output_path: Zielpfad der EPUB-Datei.
        articles_per_page: Wie viele Artikel pro EPUB-Seite zusammengefasst werden.
        use_a4_css: Wenn True, wird ein einfaches A4-Stylesheet eingebunden.

        extra_chapters: Optionale Liste zusätzlicher Kapitel als Tuple
            ``(title, html_content)``.

        todos: Optionale Liste von TodoItems, die als letztes Kapitel eingefügt werden.
        weather_infos: Optionale Wettervorhersageeinträge, die als eigenes Kapitel eingefügt werden.
        quote_of_the_day: Optionaler Motivationstext als Einleitungsseite.
        quote_author: Autor des Zitats, falls vorhanden.

    """
    book = epub.EpubBook()
    book.set_identifier("newsletter")
    book.set_title("Newsletter")
    book.set_language("de")

    chapters = []

    style_item = None
    if use_a4_css:
        style_item = epub.EpubItem(
            uid="style_a4",
            file_name="style/a4.css",
            media_type="text/css",
            content=_build_a4_style(),
        )
        book.add_item(style_item)


    if extra_chapters:
        for idx, (title, html) in enumerate(extra_chapters, start=1):
            c = epub.EpubHtml(
                title=title,
                file_name=f"extra_{idx}.xhtml",
                lang="de",
            )
            if use_a4_css and style_item:
                c.content = (
                    f"<html><head><link rel='stylesheet' href='../style/a4.css' /></head><body>{html}</body></html>"
                )
            else:
                c.content = html
            if style_item:
                c.add_item(style_item)
            book.add_item(c)
            chapters.append(c)

    chapter_count = len(chapters)
    if weather_infos:
        weather_html_parts = []
        for info in weather_infos:
            snippet = info.forecast_snippet or ""
            weather_html_parts.append(f"<p>{snippet}</p>")
        weather_content = "".join(weather_html_parts)
        c = epub.EpubHtml(
            title="Wettervorhersage",
            file_name="weather.xhtml",
            lang="de",
        )
        c.content = weather_content
        if style_item:
            c.add_item(style_item)
        book.add_item(c)
        chapters.append(c)

    if quote_of_the_day:
        quote_chapter = epub.EpubHtml(title="Zitat des Tages", file_name="quote.xhtml", lang="de")
        content = f"<h1>Zitat des Tages</h1><p>{quote_of_the_day}</p>"
        if quote_author:
            content += f"<p>- {quote_author}</p>"
        quote_chapter.content = content
        if style_item:
            quote_chapter.add_item(style_item)
        book.add_item(quote_chapter)
        chapters.append(quote_chapter)


    for start in range(0, len(articles), articles_per_page):
        batch = articles[start : start + articles_per_page]
        idx = chapter_count + (start // articles_per_page) + 1

        c = epub.EpubHtml(
            title=batch[0].title or f"Artikel {idx}",
            file_name=f"chap_{idx}.xhtml",
            lang="de",
        )
        parts = []
        for art in batch:
            summary = art.summary.replace("\n", "<br/>") if art.summary else ""

            article_html = ""
            if art.article_text:
                cleaned_text = art.article_text.replace("\n", "<br/>")
                article_html = f"<div>{cleaned_text}</div>"
            parts.append(f"<h1>{art.title}</h1><p>{summary}</p>{article_html}")

        content = "".join(parts)
        if use_a4_css and style_item:
            c.content = f"<html><head><link rel='stylesheet' href='../style/a4.css' /></head><body>{content}</body></html>"
        else:
            c.content = content
        if style_item:
            c.add_item(style_item)

        book.add_item(c)
        chapters.append(c)

    if events:
        c = epub.EpubHtml(title="Termine", file_name="events.xhtml", lang="de")
        parts = []
        for evt in events:
            start = evt.start_time.strftime("%Y-%m-%d %H:%M") if evt.start_time else ""
            end = evt.end_time.strftime("%Y-%m-%d %H:%M") if evt.end_time else ""
            time_str = f"{start} - {end}" if start or end else ""
            parts.append(f"<p><b>{evt.summary}</b><br/>{time_str}</p>")
        c.content = "<h1>Termine</h1>" + "".join(parts)

        book.add_item(c)
        chapters.append(c)

    if todos:
        todo_chap = epub.EpubHtml(
            title="Todo-Liste",
            file_name="chap_todos.xhtml",
            lang="de",
        )
        items = "".join(f"<li>{t.content}</li>" for t in todos)
        todo_chap.content = f"<h1>Todo-Liste</h1><ul>{items}</ul>"
        if style_item:
            todo_chap.add_item(style_item)
        book.add_item(todo_chap)
        chapters.append(todo_chap)

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters

    epub.write_epub(output_path, book)
    return output_path

