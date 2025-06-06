from src.agents.llm_processors.event_filter_agent import EventFilterAgent
from src.models.data_models import Event

class DummyChain:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = 0
    def invoke(self, *args, **kwargs):
        out = self.outputs[self.calls]
        self.calls += 1
        return out

def test_event_filter(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    agent = EventFilterAgent()
    agent.chain = DummyChain(["7", "3"])
    events = [Event(summary="A", source="x"), Event(summary="B", source="x")]
    filtered = agent.process_batch(events)
    assert len(filtered) == 1
    assert filtered[0].summary == "A"
