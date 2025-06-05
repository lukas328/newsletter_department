from ebooklib import epub
from typing import List
from src.models.data_models import ProcessedArticle


def generate_epub(articles: List[ProcessedArticle], output_path: str) -> str:
    """Generiert eine einfache EPUB-Datei aus verarbeiteten Artikeln."""
    book = epub.EpubBook()
    book.set_identifier("newsletter")
    book.set_title("Newsletter")
    book.set_language("de")

    chapters = []
    for idx, article in enumerate(articles, start=1):
        c = epub.EpubHtml(title=article.title or f"Artikel {idx}", file_name=f"chap_{idx}.xhtml", lang="de")
        summary = article.summary.replace('\n', '<br/>') if article.summary else ''
        content = f"<h1>{article.title}</h1><p>{summary}</p>"
        c.content = content
        book.add_item(c)
        chapters.append(c)

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ['nav'] + chapters

    epub.write_epub(output_path, book)
    return output_path
