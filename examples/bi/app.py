"""Offline by default; --live opts into Gemini and the configured SQL Server."""
import argparse
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService
from examples.runtime import APP_NAME, new_identity, run_turn
from examples.bi.pipeline import make_workflow


async def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="?", default="total sales by country")
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--chart", type=Path, default=Path("artifacts/bike-chart.html"))
    args = parser.parse_args()
    workflow, engine = make_workflow(live=args.live)
    try:
        sessions, identity = InMemorySessionService(), new_identity()
        answer, _ = await run_turn(workflow, args.question, identity, sessions)
        print(answer)
        session = await sessions.get_session(app_name=APP_NAME, **identity)
        if session.state.get("chart"):
            import altair as alt
            args.chart.parent.mkdir(parents=True, exist_ok=True)
            alt.Chart.from_dict(session.state["chart"]).save(args.chart)
            print(f"Chart saved to {args.chart.resolve()}")
    finally:
        engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
