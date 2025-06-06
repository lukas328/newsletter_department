import logging
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from src.models.data_models import Event
from .base_processor import BaseLLMProcessor

logger = logging.getLogger(__name__)

class EventFilterAgent(BaseLLMProcessor):
    """Filters events based on interest using an LLM."""

    def __init__(self, threshold: float = 5.0, model_name: str | None = None, temperature: float = 0):
        super().__init__(model_name=model_name, temperature=temperature)
        self.threshold = threshold
        self.prompt_template = ChatPromptTemplate.from_template(
            "Rate from 1 (boring) to 10 (exciting) how interesting this event is for a Zurich tech newsletter.\n" \
            "Return only the number.\nEVENT:\n{event_text}"
        )
        self.chain = self.prompt_template | self.llm | StrOutputParser()
        logger.info("EventFilterAgent initialized with threshold %s", self.threshold)

    def _score_event(self, event: Event) -> float:
        event_text = f"Title: {event.summary}\nDescription: {event.description or ''}\nLocation: {event.location or ''}"
        try:
            output = self.chain.invoke({"event_text": event_text})
            score = float(output.strip())
        except Exception as exc:
            logger.error("Error scoring event '%s': %s", event.summary, exc, exc_info=True)
            return 0.0
        return score

    def process_batch(self, events: List[Event]) -> List[Event]:
        if self.llm is None:
            logger.error("LLM not available for EventFilterAgent. Returning events unchanged.")
            return events
        filtered: List[Event] = []
        for evt in events:
            score = self._score_event(evt)
            if score >= self.threshold:
                filtered.append(evt)
        logger.info("EventFilterAgent kept %d of %d events", len(filtered), len(events))
        return filtered
