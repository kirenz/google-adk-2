import math
import pandas as pd
import pytest
import sqlglot
from examples.first_agent.agent import calculate_order_total
from examples.bi.guards import validate_sql
from examples.bi.charts import ChartSpec, build_chart
from examples.bi.data import demo_engine, execute_select
from examples.bi.pipeline import make_workflow
from examples.function_workflow.agent import root_agent
from examples.runtime import APP_NAME, new_identity, run_turn
from google.adk.sessions import InMemorySessionService


def test_decimal_tool():
    assert calculate_order_total(0.335, 3)["total"] == "1.01"
    for price, quantity in [(-1, 2), (1, -1), (math.inf, 1), (math.nan, 1)]:
        with pytest.raises(ValueError):
            calculate_order_total(price, quantity)


@pytest.mark.parametrize("sql", [
    "DELETE FROM sales_demo", "SELECT country FROM sales_demo; DELETE FROM sales_demo",
    "SELECT country INTO stolen FROM sales_demo", "SELECT * FROM sales_demo",
    "SELECT country FROM private_table", "SELECT country FROM sales_demo UNION SELECT country FROM sales_demo",
    "WITH x AS (SELECT country FROM sales_demo) SELECT country FROM x",
    "SELECT country FROM (SELECT country FROM sales_demo) AS x",
])
def test_sql_rejects_unsafe_or_out_of_scope(sql):
    with pytest.raises(ValueError):
        validate_sql(sql, "sqlite", {"sales_demo"})


@pytest.mark.parametrize("query,dialect", [
    ("SELECT country FROM sales_demo LIMIT 99999 OFFSET 9", "sqlite"),
    ("SELECT TOP 99999 country FROM sales_demo", "tsql"),
    ("SELECT TOP 10 PERCENT country FROM sales_demo", "tsql"),
    ("SELECT TOP 10 WITH TIES country FROM sales_demo ORDER BY country", "tsql"),
])
def test_row_limit_is_replaced(query, dialect):
    safe = validate_sql(query, dialect, {"sales_demo"})
    tree = sqlglot.parse_one(safe, read=dialect)
    assert tree.args["limit"].expression.this == "100"
    assert not tree.args.get("offset")
    assert "PERCENT" not in safe and "TIES" not in safe


def test_fixture_empty_error_and_fetch_cap():
    engine = demo_engine()
    try:
        assert execute_select(engine, "SELECT country FROM sales_demo WHERE 1=0").empty
        with pytest.raises(Exception):
            execute_select(engine, "SELECT nonexistent FROM sales_demo")
        with pytest.raises(ValueError):
            execute_select(engine, "WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<101) SELECT x FROM n")
    finally:
        engine.dispose()


def test_chart_validation():
    frame = pd.DataFrame({"country": ["DE", "US"], "sales": [2.0, 1.0]})
    assert build_chart(frame, ChartSpec(kind="bar", x="country", y="sales")).to_dict()["mark"]["type"] == "bar"
    for target, spec in [
        (frame, dict(kind="bar", x="missing", y="sales")),
        (frame, dict(kind="bar", x="sales", y="country")),
        (frame, dict(kind="line", x="country", y="sales")),
        (frame.iloc[:0], dict(kind="bar", x="country", y="sales")),
    ]:
        with pytest.raises(ValueError):
            build_chart(target, ChartSpec(**spec))
    with pytest.raises(ValueError):
        ChartSpec(kind="python", x="country", y="sales")


@pytest.mark.asyncio
async def test_actual_offline_workflow_and_isolated_sessions():
    sessions = InMemorySessionService()
    first, second = new_identity(), new_identity()
    assert first != second
    answer, _ = await run_turn(root_agent, "  hello   world  ", first, sessions)
    assert "Words: 2" in answer
    await run_turn(root_agent, "different", second, sessions)
    a = await sessions.get_session(app_name=APP_NAME, **first)
    b = await sessions.get_session(app_name=APP_NAME, **second)
    assert a.id != b.id
    assert any("hello" in str(event.content) for event in a.events)
    assert all("hello" not in str(event.content) for event in b.events)


@pytest.mark.asyncio
async def test_actual_offline_bi_workflow():
    workflow, engine = make_workflow()
    sessions, identity = InMemorySessionService(), new_identity()
    try:
        answer, _ = await run_turn(workflow, "total sales by country", identity, sessions)
        session = await sessions.get_session(app_name=APP_NAME, **identity)
        assert "EUR 2,000" in answer
        assert session.state["rows"][0] == {"country": "Germany", "total_sales": 2000.0}
        assert session.state["chart"]["mark"]["type"] == "bar"
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_fake_model_to_deterministic_function():
    from google.adk import Agent, Workflow
    from google.adk.workflow import START
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types
    from examples.agent_workflow.agent import Order, total, present

    class FakeOrderModel(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text='{"unit_price": 499.95, "quantity": 3}')]))

    agent = Agent(name="fake_extract", model=FakeOrderModel(model="offline-test"), output_schema=Order)
    workflow = Workflow(name="fake_order_workflow", edges=[(START, agent, total, present)])
    answer, _ = await run_turn(workflow, "3 bikes at EUR 499.95", new_identity(), InMemorySessionService())
    assert "EUR 1499.85" in answer


@pytest.mark.asyncio
@pytest.mark.parametrize("case", ["empty", "error"])
async def test_bi_no_chart_for_empty_or_error(monkeypatch, case):
    import examples.bi.pipeline as pipeline
    if case == "empty":
        monkeypatch.setattr(pipeline, "execute_select", lambda *args, **kwargs: pd.DataFrame(columns=["country", "total_sales"]))
    else:
        def fail(*args, **kwargs):
            raise ValueError("Unsafe generated SQL")
        monkeypatch.setattr(pipeline, "validate_sql", fail)
    workflow, engine = pipeline.make_workflow()
    sessions, identity = InMemorySessionService(), new_identity()
    try:
        answer, _ = await run_turn(workflow, "total sales by country", identity, sessions)
        session = await sessions.get_session(app_name=APP_NAME, **identity)
        assert session.state["chart"] is None
        assert session.state["rows"] == []
        assert "No" in answer
    finally:
        engine.dispose()


def test_sql_alias_keeps_qualified_allowlist():
    safe = validate_sql("SELECT s.Country FROM dbo.CourseSales AS s", "tsql", {" dbo.CourseSales "})
    assert "AS s" in safe and "TOP 100" in safe
    for table in ("dbo.PrivateSales", "other.CourseSales", "other_database.dbo.CourseSales", "remote.other_database.dbo.CourseSales"):
        with pytest.raises(ValueError):
            validate_sql(f"SELECT s.Country FROM {table} AS s", "tsql", {"dbo.CourseSales"})


def test_order_negative_and_ambiguous_values_refused():
    from examples.agent_workflow.agent import Order, total
    for order in ({"unit_price": -1, "quantity": 2}, {"unit_price": 2, "quantity": -1}, {"unit_price": True, "quantity": 2}, {"unit_price": 2, "quantity": 1.5}):
        with pytest.raises(ValueError):
            Order(**order)
    with pytest.raises(ValueError):
        calculate_order_total(True, 2)
    assert total(Order(unit_price=2, quantity=3))["total"] == "6.00"


@pytest.mark.asyncio
async def test_fake_model_missing_input_never_calculates_total():
    from google.adk import Agent, Workflow
    from google.adk.workflow import START
    from google.adk.models.base_llm import BaseLlm
    from google.adk.models.llm_response import LlmResponse
    from google.genai import types
    from examples.agent_workflow.agent import Order, total, present

    class MissingPriceModel(BaseLlm):
        async def generate_content_async(self, llm_request, stream=False):
            yield LlmResponse(content=types.Content(role="model", parts=[types.Part(text='{"unit_price": null, "quantity": 3}')]))

    agent = Agent(name="fake_missing", model=MissingPriceModel(model="offline-test"), output_schema=Order)
    workflow = Workflow(name="missing_order_workflow", edges=[(START, agent, total, present)])
    answer, events = await run_turn(workflow, "3 bikes", new_identity(), InMemorySessionService())
    assert "Please provide the unit price in EUR" in answer
    assert "No total has been calculated" in answer
    assert "Order total: EUR" not in answer
    assert total(Order(quantity=3)) == {"status": "needs_input", "missing_fields": ["unit_price"]}


@pytest.mark.asyncio
async def test_rejected_bi_chart_does_not_emit_explanation(monkeypatch):
    import examples.bi.pipeline as pipeline
    def reject(*args, **kwargs):
        raise ValueError("Missing chart field")
    monkeypatch.setattr(pipeline, "build_chart", reject)
    workflow, engine = pipeline.make_workflow()
    sessions, identity = InMemorySessionService(), new_identity()
    try:
        answer, _ = await run_turn(workflow, "total sales by country", identity, sessions)
        session = await sessions.get_session(app_name=APP_NAME, **identity)
        assert answer == "Chart rejected: Missing chart field"
        assert "EUR 2,000" not in answer
        assert session.state["chart"] is None
    finally:
        engine.dispose()


@pytest.mark.asyncio
async def test_fixture_available_from_ui_worker_thread():
    import asyncio
    from examples.bi.data import DEMO_SQL
    engine = demo_engine()
    try:
        frame = await asyncio.to_thread(execute_select, engine, DEMO_SQL)
        assert frame.iloc[0].to_dict() == {"country": "Germany", "total_sales": 2000.0}
    finally:
        engine.dispose()
