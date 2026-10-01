"""Synthetic SQLite fixture and an explicitly configured SQL Server connection."""
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from examples.bi.guards import MAX_ROWS

DEMO_SCHEMA = "sales_demo(country TEXT, net_sales REAL, order_date TEXT, product_name TEXT, quantity INTEGER)"
DEMO_SQL = "SELECT country, SUM(net_sales) AS total_sales FROM sales_demo GROUP BY country ORDER BY total_sales DESC"


def demo_engine():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE synthetic_sales (country TEXT, net_sales REAL, order_date TEXT, product_name TEXT, quantity INTEGER)"))
        connection.execute(text("INSERT INTO synthetic_sales VALUES (:country,:net_sales,:order_date,:product_name,:quantity)"), [
            dict(country="Germany", net_sales=1200.0, order_date="2026-01-02", product_name="Touring bike", quantity=2),
            dict(country="Germany", net_sales=800.0, order_date="2026-01-05", product_name="City bike", quantity=2),
            dict(country="USA", net_sales=1500.0, order_date="2026-01-03", product_name="Touring bike", quantity=3),
            dict(country="France", net_sales=500.0, order_date="2026-01-04", product_name="City bike", quantity=1),
        ])
        connection.execute(text("CREATE VIEW sales_demo AS SELECT country, net_sales, order_date, product_name, quantity FROM synthetic_sales"))
        connection.exec_driver_sql("PRAGMA query_only = ON")
    return engine


def live_settings():
    required = ["SQLSERVER_URL", "BI_SCHEMA", "BI_ALLOWED_VIEWS"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise ValueError("Live mode requires " + ", ".join(missing))
    if os.getenv("BI_READ_ONLY_ACCOUNT_CONFIRMED") != "yes":
        raise ValueError("Confirm the dedicated SELECT-only database account with BI_READ_ONLY_ACCOUNT_CONFIRMED=yes.")
    return os.environ["BI_SCHEMA"], {view.strip() for view in os.environ["BI_ALLOWED_VIEWS"].split(",") if view.strip()}


def live_engine():
    live_settings()
    # A SQL Server ODBC driver must already be installed separately.
    return create_engine(os.environ["SQLSERVER_URL"], pool_pre_ping=True, connect_args={"timeout": 10})


def execute_select(engine, sql: str, live: bool = False) -> pd.DataFrame:
    with engine.connect() as connection:
        if live:
            connection.exec_driver_sql("SET LOCK_TIMEOUT 5000")
            raw = connection.connection.driver_connection
            raw.timeout = 15  # pyodbc query timeout, independent from connect timeout.
        result = connection.execute(text(sql))
        columns = list(result.keys())
        # Fetching also enforces the application bound even if SQL generation changes.
        rows = result.fetchmany(MAX_ROWS + 1)
        if len(rows) > MAX_ROWS:
            raise ValueError("The database returned more than the permitted row count.")
        return pd.DataFrame(rows, columns=columns)
