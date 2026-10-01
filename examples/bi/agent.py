"""Offline fixture entry point for adk web; use Gradio to display the chart."""
from examples.bi.pipeline import make_workflow

root_agent, engine = make_workflow()
