import logging
from typing import List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.agents.llm_processors.base_processor import BaseLLMProcessor
from src.models.data_models import Artwork

logger = logging.getLogger(__name__)

class ArtDescriptionAgent(BaseLLMProcessor):
    """Erzeugt eine kurze Beschreibung eines Kunstwerks."""

    def __init__(self, model_name: Optional[str] = None, temperature: float = 0.7):
        super().__init__(model_name=model_name, temperature=temperature)
        self.prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "Du bist ein Kunstexperte und gibst prägnante Beschreibungen.",
            ),
            (
                "human",
                """
Beschreibe das Kunstwerk in wenigen Sätzen. Erwähne den Künstler, den Ort, an dem es ausgestellt ist, und ordne es einer Kunstepoche zu.
Titel: {title}
Künstler: {artist}
Ort: {location}
Epoche: {epoch}
""",
            ),
        ])
        self.chain = self.prompt | self.llm | StrOutputParser()
        logger.info(
            f"ArtDescriptionAgent initialisiert mit Modell '{self.model_name}'."
        )

    def describe_artwork(self, art: Artwork) -> str:
        return self.chain.invoke({
            "title": art.title,
            "artist": art.artist or "Unbekannt",
            "location": art.location or "Unbekannt",
            "epoch": art.epoch or "Unbekannt",
        }).strip()

    def process_batch(self, artworks: List[Artwork]) -> List[str]:
        return [self.describe_artwork(a) for a in artworks]
