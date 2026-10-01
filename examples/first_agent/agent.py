"""One model, one deterministic Python tool. Requires a Gemini API key."""
import os
from decimal import Decimal, ROUND_HALF_UP
from dotenv import load_dotenv
from google.adk import Agent

load_dotenv()


def calculate_order_total(unit_price: float, quantity: int) -> dict:
    """Calculate an order's total in EUR; price and quantity must be nonnegative."""
    if isinstance(unit_price, bool) or not isinstance(unit_price, (int, float)):
        raise ValueError("Price must be a numeric amount, not a boolean or string.")
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity < 0 or quantity > 10000 or unit_price < 0:
        raise ValueError("Use a nonnegative price and a quantity from 0 to 10000.")
    price = Decimal(str(unit_price))
    if not price.is_finite():
        raise ValueError("Price must be finite.")
    total = (price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"currency": "EUR", "total": str(total), "quantity": quantity}


root_agent = Agent(
    name="order_assistant",
    model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
    instruction="Use calculate_order_total for all order arithmetic. Ask for missing values. Explain the tool result briefly; never invent a price.",
    tools=[calculate_order_total],
)
