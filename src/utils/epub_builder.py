from typing import List
from ebooklib import epub
from src.models.data_models import ProcessedArticle
import logging

logger = logging.getLogger(__name__)

def build_newsletter_epub(articles: List[ProcessedArticle], output_path: str) -> str:
    """Create an EPUB newsletter from processed articles.

    Args:
        articles: List of processed articles with title, summary, etc.
        output_path: File path where the EPUB will be written.

    Returns:
        The path to the written EPUB file.
    """
    book = epub.EpubBook()
    book.set_identifier("newsletter")
    book.set_title("Newsletter")
    book.set_language("de")
    book.add_author("Automatisierter Newsletter")

    chapters = []
    for idx, art in enumerate(articles, start=1):
        title = art.title or f"Artikel {idx}"
        html_content = (
            f"<h1>{title}</h1>"
            f"<p><strong>Quelle:</strong> {art.source_name or ''}</p>"
            f"<p><strong>Kategorie:</strong> {art.category or ''}</p>"
            f"<p>{art.summary}</p>"
        )
        if art.url:
            html_content += f"<p><a href='{art.url}'>Originalartikel</a></p>"
        chapter = epub.EpubHtml(title=title, file_name=f"chap_{idx}.xhtml", lang="de")
        chapter.content = html_content
        book.add_item(chapter)
        chapters.append(chapter)

    book.toc = tuple(chapters)
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav"] + chapters

    epub.write_epub(output_path, book)
    logger.info(f"EPUB Newsletter erstellt: {output_path}")
    return output_path
