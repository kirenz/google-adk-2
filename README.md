# Google ADK 2

An English Quarto course book and runnable Python examples for Google ADK **2.10.0**. The learning path follows the earlier MIS Agentic AI course: preparation, agents and tools, context and runtime, workflows, Gradio, and a SQL analytics project. The chapters and examples are self-contained.

[Read the course book](https://kirenz.github.io/google-adk-2/).

## Start locally

Python 3.12 is selected through `.python-version`. [uv](https://docs.astral.sh/uv/getting-started/installation/) manages the environment and uses the committed lockfile. Run every command from this folder:

```bash
git clone https://github.com/kirenz/google-adk-2.git
cd google-adk-2
uv sync --extra dev
uv run pytest
uv run python -m examples.run_workflow
uv run python -m examples.bi.app
uv run python -m examples.bi.gradio_app
```

The last command starts the BI interface on localhost. The offline BI path accepts exactly `total sales by country`; it uses four synthetic SQLite rows and produces Germany 2000, USA 1500, France 500. It is a deterministic demonstration, not a model answering arbitrary questions. Generated charts are saved to `artifacts/`.

## Read the book

Install [Quarto](https://quarto.org/docs/get-started/), then:

```bash
quarto preview
```

The local preview is at `http://localhost:4202`. `quarto render` builds the static book in `_book/`. Rendering never executes the Python snippets or model calls. `index.qmd` describes learning outcomes and deliverables. Semester dates and assessment weights are intentionally not inherited from the old course.

## Model-backed exercises

Copy the provided configuration example without committing credentials:

```bash
cp .env.example .env
```

Windows PowerShell uses `Copy-Item .env.example .env`. Set a local Gemini Developer API key and a model available to that account. `GEMINI_MODEL=gemini-flash-latest` is a changing provider alias; record an explicit available model ID for a reproducible experiment when possible.

```bash
uv run adk web examples
uv run python -m examples.run_agent "What is the total for 3 bikes at EUR 499.95 each?"
uv run python -m examples.gradio_app
```

In ADK Web, choose `first_agent` for the tool-using agent, `function_workflow` for the offline graph, `agent_workflow` for structured extraction and calculation, or `bi` for the synthetic BI graph. The Python package name in that selector need not equal the internal agent's name. Running an Agent contacts Gemini and is subject to provider quotas and pricing. Offline tests use synthetic data and a fake model, not the account's API key.

## SQL Server extension

The Preparation chapters cover [Accounts](chapters/accounts.qmd), [Windows](chapters/windows-setup.qmd), [macOS](chapters/mac-setup.qmd), [VS Code](chapters/mssql-vscode.qmd), and [Server Connection](chapters/mssql-connection.qmd). The server chapter verifies connectivity independently of Gemini; the BI chapter adds permitted views and agent query validation. The offline route does not require pyodbc. For live SQL Server use:

```bash
uv sync --extra dev --extra sqlserver
uv run python -m examples.bi.app --live "A QUESTION ABOUT THE APPROVED SCHEMA"
```

Configure `SQLSERVER_URL`, `BI_SCHEMA`, `BI_ALLOWED_VIEWS`, and `BI_READ_ONLY_ACCOUNT_CONFIRMED` in `.env` first. The account must be provisioned independently with SELECT-only access to approved views. Parser checks are an additional validation layer, not a substitute for database permissions. Live results are sent to the configured model for chart planning and explanation.

## Layout

```text
google-adk-2/
├── index.qmd, references.qmd, _quarto.yml, theme.scss
├── chapters/        # Learning chapters and platform-specific preparation
├── images/          # Generated illustrations and provenance
├── examples/        # Agents, graphs, Runner, Gradio, BI
├── tests/           # Offline behavior and integration checks
├── .env.example     # Shareable configuration placeholders
├── pyproject.toml, uv.lock, .python-version
└── VALIDATION.md    # Checks performed and remaining live checks
```

The previous courses and examples were read as source material and remain unchanged. Source code is hosted in `kirenz/google-adk-2`; the book is published with Quarto to the `gh-pages` branch. The publishing workflow renders static pages without executing model calls. Publication changes the public course book, not a running agent or database service.
