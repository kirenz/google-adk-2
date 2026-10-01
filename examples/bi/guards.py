"""SQL syntax checks are one layer; database permissions remain essential."""
import sqlglot
from sqlglot import exp

MAX_ROWS = 100


def validate_sql(sql: str, dialect: str, allowed_tables: set[str]) -> str:
    statements = sqlglot.parse(sql, read=dialect)
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise ValueError("Exactly one SELECT is allowed (no UNION or commands).")
    tree = statements[0]
    # Deliberately narrow grammar for the first BI exercise: no CTEs or subqueries.
    forbidden = (exp.Into, exp.Subquery, exp.With, exp.Star)
    if any(tree.find(kind) for kind in forbidden):
        raise ValueError("SELECT INTO, subqueries, CTEs and SELECT * are not allowed.")
    allowed = {name.strip().casefold() for name in allowed_tables}
    tables = list(tree.find_all(exp.Table))
    def identifier(table):
        reference = table.copy()
        reference.set("alias", None)
        return reference.sql(dialect=dialect).casefold()

    if not tables or any(identifier(table) not in allowed for table in tables):
        raise ValueError("Use only the configured read-only views.")
    # Reject anonymous/dialect-specific function calls, remote data access included.
    if tree.find(exp.Anonymous):
        raise ValueError("Unrecognized SQL functions are not allowed.")
    if tree.args.get("locks"):
        raise ValueError("Locking clauses are not allowed.")
    tree.set("limit", exp.Limit(expression=exp.Literal.number(MAX_ROWS)))
    # TOP PERCENT / WITH TIES and excessive TOP/LIMIT are replaced, not trusted.
    tree.set("offset", None)
    return tree.sql(dialect=dialect)
