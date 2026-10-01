"""Render a validated chart specification; never execute model-generated Python."""
from typing import Literal
import math
import altair as alt
import pandas as pd
from pydantic import BaseModel, ConfigDict


class ChartSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["bar", "line", "point"]
    x: str
    y: str
    title: str = "Query result"


def build_chart(frame: pd.DataFrame, spec: ChartSpec):
    if frame.empty:
        raise ValueError("No rows: a chart cannot be built.")
    if len(frame.columns) != len(set(frame.columns)):
        raise ValueError("Duplicate column names are not supported.")
    if spec.x not in frame or spec.y not in frame:
        raise ValueError("Chart fields must be columns in the query result.")
    if not pd.api.types.is_numeric_dtype(frame[spec.y]):
        raise ValueError("The y field must be numeric.")
    if frame[spec.y].isna().any() or not frame[spec.y].map(math.isfinite).all():
        raise ValueError("The y field contains missing or nonfinite values.")
    x_type = "quantitative" if pd.api.types.is_numeric_dtype(frame[spec.x]) else "nominal"
    if spec.kind == "line" and not (pd.api.types.is_numeric_dtype(frame[spec.x]) or pd.api.types.is_datetime64_any_dtype(frame[spec.x])):
        raise ValueError("Line charts need numeric or parsed datetime x values.")
    if pd.api.types.is_datetime64_any_dtype(frame[spec.x]):
        x_type = "temporal"
    chart = alt.Chart(frame).encode(x=alt.X(field=spec.x, type=x_type), y=alt.Y(field=spec.y, type="quantitative"))
    chart = {"bar": chart.mark_bar, "line": chart.mark_line, "point": chart.mark_point}[spec.kind]()
    return chart.properties(title=spec.title[:120], width="container", height=280)
