"""A real ADK Workflow with only functions: no model or API key required."""
from google.adk import Event, Workflow
from google.adk.workflow import START


def normalize(node_input: str) -> str:
    return " ".join(node_input.split()).strip()


def measure(node_input: str) -> dict:
    return {"text": node_input, "word_count": len(node_input.split())}


def report(node_input: dict):
    yield Event(message=f"Normalized text: {node_input['text']}\nWords: {node_input['word_count']}")
    yield Event(output=node_input)


root_agent = Workflow(name="text_workflow", edges=[(START, normalize, measure, report)])
