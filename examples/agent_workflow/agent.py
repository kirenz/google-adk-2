"""Model extracts an order; Python calculates and formats the result."""
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google.adk import Agent, Event, Workflow
from google.adk.workflow import START
from examples.first_agent.agent import calculate_order_total

load_dotenv()


class Order(BaseModel):
    unit_price: float | None = Field(default=None, ge=0, strict=True)
    quantity: int | None = Field(default=None, ge=0, le=10000, strict=True)


extract_order = Agent(
    name="extract_order", model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
    instruction="Extract only the explicit unit price in EUR and integer quantity. Set missing values to null. Never guess values. Return structured data; a later Python step asks for missing input.",
    output_schema=Order,
)


def total(node_input: Order) -> dict:
    missing = [field for field in ("unit_price", "quantity") if getattr(node_input, field) is None]
    if missing:
        return {"status": "needs_input", "missing_fields": missing}
    return {"status": "complete", **calculate_order_total(node_input.unit_price, node_input.quantity)}


def present(node_input: dict):
    if node_input["status"] == "needs_input":
        labels = {"unit_price": "unit price in EUR", "quantity": "quantity"}
        missing = " and ".join(labels[field] for field in node_input["missing_fields"])
        yield Event(message=f"Please provide the {missing}. No total has been calculated.")
    else:
        yield Event(message=f"Order total: EUR {node_input['total']} ({node_input['quantity']} items).")
    yield Event(output=node_input)


root_agent = Workflow(name="order_workflow", edges=[(START, extract_order, total, present)])
