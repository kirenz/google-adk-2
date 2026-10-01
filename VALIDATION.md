# Validation record

Checked locally on 2026-10-01 with Python 3.12.9, google-adk 2.10.0, Gradio 6.29.0, and Quarto 1.8.27. The full software resolution is in `uv.lock`.

## Completed checks

- `uv sync --extra dev` installed the base course and test environment.
- `uv run pytest`: **25 passed**. Tests cover decimal arithmetic, missing structured input, SQL refusals and row-cap replacement, exact source allowlisting with aliases, chart validity, actual ADK graph execution, fake-model handoffs, empty/error states, session separation, and querying the synthetic SQLite fixture from a worker thread.
- Both offline CLIs ran without an API key. The text graph reported four words for the default input. The BI graph returned Germany 2000, USA 1500, France 500 and saved the chart HTML.
- `quarto render` built all 14 pages (syllabus, twelve chapters, references). The render does not execute Python examples.
- A local generated-HTML audit checked **576 relative links and resource references with zero missing targets**. Thirty external source/reference links returned HTTP 200 using system curl. References added for the public course are checked during publication.
- The two evaluation JSON files parsed against ADK's installed `EvalSet` and `EvalConfig` models. Parsing establishes schema compatibility, not a successful live evaluation.
- ADK Web at a temporary local port discovered `first_agent`, `function_workflow`, `agent_workflow`, and `bi`.
- Browser checks confirmed the course cover, sidebar, text and Mermaid rendering. The offline Gradio BI interface displayed the validated SQL, exact fixture table and chart. An unsupported request cleared the prior outputs.
- Generated illustrations were visually inspected and saved inside `images/` with alt text and provenance notes.

## Browser issue found and corrected

The initial Gradio request used a worker thread that received a separate in-memory SQLite connection. CLI tests passed but the interface failed. The fixture now uses `StaticPool` with cross-thread access enabled; the teaching BI interface serializes requests. An explicit worker-thread regression test and a repeated browser run verified the fix.

## Scope of evidence

Live Gemini inference, model-backed ADK evaluation, and a real Global Bike SQL Server connection have not been executed. They require locally supplied credentials, account/model access, and an actual permitted schema. The SQL Server extra and evaluation extra are resolved in the lockfile but are not prerequisites of the offline path. Windows/macOS installer instructions are linked to vendor documentation; they were not executed on a second machine.

Passing offline checks does not prove that a model extracts every question correctly, that an explanation is factual, or that a database login is read-only. Those behaviors have explicit exercises and evaluation criteria in the book.
