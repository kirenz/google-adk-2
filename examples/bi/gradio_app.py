"""Local BI UI showing the SQL, returned rows and validated chart together."""
import argparse
import logging
import altair as alt
import gradio as gr
import pandas as pd
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from examples.bi.pipeline import make_workflow
from examples.runtime import APP_NAME, new_identity, run_turn


def build_app(live=False):
    workflow, engine = make_workflow(live=live)
    sessions = InMemorySessionService()

    async def answer(question, identity):
        identity = identity or new_identity()
        try:
            reply, _ = await run_turn(workflow, question, identity, sessions)
            session = await sessions.get_session(app_name=APP_NAME, **identity)
            state = session.state
            chart = alt.Chart.from_dict(state["chart"]) if state.get("chart") else None
            return reply, state.get("sql") or "", pd.DataFrame(state.get("rows", []), columns=state.get("columns", [])), chart, identity
        except Exception as error:
            logging.getLogger(__name__).warning("BI browser request failed: %s", type(error).__name__)
            # Clear all visible outputs; never leave a previous successful chart on failure.
            return f"Request failed ({type(error).__name__}). See terminal/configuration.", "", pd.DataFrame(), None, identity

    with gr.Blocks(title="Global Bike BI teaching starter") as demo:
        identity = gr.State(value=new_identity)
        gr.Markdown("# Global Bike BI starter\n" + ("Live SQL Server. Model explanations are drafts. Verify SQL and returned rows." if live else "Offline synthetic SQLite fixture. Supported question: **total sales by country**. No arbitrary natural-language answering."))
        question = gr.Textbox(value="total sales by country", label="Question")
        submit = gr.Button("Run analysis")
        narrative = gr.Textbox(label="Explanation")
        sql = gr.Code(language="sql", label="Validated SQL")
        table = gr.Dataframe(label="Returned rows", interactive=False)
        plot = gr.Plot(label="Validated chart")
        submit.click(answer, [question, identity], [narrative, sql, table, plot, identity], concurrency_limit=1)
    # Retain ownership so callers can dispose the engine when their server exits.
    demo.bi_engine = engine
    return demo


if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    build_app(live=args.live).queue().launch(server_name="127.0.0.1", share=False)
