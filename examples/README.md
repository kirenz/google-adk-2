# Runnable examples

Run commands from the course root after `uv sync`. Python 3.12 and google-adk 2.10.0 are pinned by the course. Copy `examples/.env.example` to `.env` and fill your own Gemini key only for model examples. An installed SDK does not guarantee access to a particular model; set `GEMINI_MODEL` to a model available to your account. The `gemini-flash-latest` default is a moving alias, not a pinned model version.

| Learning step | Command | External access |
| --- | --- | --- |
| Plain tool plus Agent | `uv run python -m examples.run_agent` | Gemini |
| ADK development UI | `uv run adk web examples` | Gemini when running an Agent |
| Function-only Workflow | `uv run python -m examples.run_workflow` | None |
| Agent and function Workflow | `uv run adk run examples/agent_workflow` | Gemini |
| Local chat UI | `uv run python -m examples.gradio_app` | Gemini |
| Complete synthetic BI Workflow | `uv run python -m examples.bi.app` | None |
| Synthetic BI browser UI | `uv run python -m examples.bi.gradio_app` | None |
| Live SQL Server BI | `uv run python -m examples.bi.app --live 'YOUR QUESTION'` | Gemini + SQL Server |
| Live BI browser UI | `uv run python -m examples.bi.gradio_app --live` | Gemini + SQL Server |
| Offline checks | `uv run pytest` | None |

The first tool uses decimal arithmetic. In `function_workflow`, ADK executes three ordinary functions connected by edges. In `agent_workflow`, the model extracts a structured order with nullable fields. Python asks for missing values without computing a total; complete valid orders are calculated deterministically. A subsequent turn must include the complete order, as this small Workflow does not merge partially supplied fields across turns. Function nodes receive the previous node's output through `node_input`. A node's `Event.output` is passed to its successor; `Event.message` is displayed to the user.

The Gradio apps bind to localhost and do not create a public share link. `gr.State(value=new_identity)` creates a distinct ADK user and session identity for each browser session. A shared in-memory session service stores histories under those identities; it is not durable storage or authentication. Clearing the chat starts a new ADK identity; old histories remain in memory until restart. Restarting the process loses histories. Do not use this teaching identity mechanism as production user isolation.

## BI: fixture first, real schema second

The SQLite engine shares one in-memory connection across UI worker threads (`StaticPool` and `check_same_thread=False`); the BI UI serializes analysis requests. Offline mode runs the real ADK Workflow with fixed proposals and a four-row **synthetic** SQLite fixture. It supports exactly `total sales by country`, produces Germany 2000, USA 1500 and France 500, and writes `artifacts/bike-chart.html`. It demonstrates SQL validation, execution, chart planning and rendering, not arbitrary natural-language understanding. `sales_demo` is a course fixture, not an assertion about actual Global Bike tables or business results.

Live mode replaces the two fixed proposal functions with Agents. The flow is model SQL proposal → deterministic SQL gate and query → model chart specification/explanation → deterministic chart validation and rendering. The model receives the returned rows, so database results leave the machine for the model provider. Use only data approved for that use. No model-generated Python is executed. The explanation is a draft grounded by instruction in the returned rows; this is not a factual guarantee. Inspect the SQL, rows and chart together.

Before `--live`, supply a real SQL Server connection, schema and exact view allowlist through the variables in `.env.example`. Install the appropriate Microsoft ODBC driver outside the Python environment. Global Bike installations differ: inspect your actual database and create approved read-only views with the database administrator. No live database has been assumed or bundled. Use a dedicated login that can SELECT only the necessary views and cannot change data or execute stored procedures. `BI_READ_ONLY_ACCOUNT_CONFIRMED=yes` records your confirmation; the application cannot prove your login permissions.

The SQL gate deliberately accepts one simple SELECT with explicit fields. It rejects commands, multiple statements, UNION, SELECT INTO, CTEs, subqueries, SELECT *, unknown functions and tables outside the allowlist. It rewrites TOP/LIMIT to 100 rows, removes offsets, and bounds driver fetching as well. Live connections have connection, lock and query timeouts. These checks limit this exercise's surface, but parser validation is not a security boundary: read-only database permissions, network controls and approved views are still required. A row cap limits returned rows, not the work performed by an aggregate or join; an ordered top 100 result may omit groups.

Empty queries produce no chart. SQL failures clear previous results. Invalid chart specifications are rejected locally. Only bar, line and point charts with existing fields and numeric y values are accepted. Category x values are allowed for bars/points; lines require numeric or parsed datetime x. The starter does not inspect the live schema automatically, repair unsafe queries, install a driver, deploy a UI, or establish production authentication.
