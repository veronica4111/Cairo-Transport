"""Small utility helpers shared across the Cairo transport project."""

from __future__ import annotations

try:
    from tabulate import tabulate as _tabulate
except ModuleNotFoundError:
    def _tabulate(rows, headers=(), tablefmt: str | None = None):  # type: ignore[no-redef]
        """Fallback plain-text table formatter when tabulate is unavailable."""
        table_rows = [list(headers)] + [list(map(str, row)) for row in rows]
        widths = [max(len(str(row[index])) for row in table_rows) for index in range(len(table_rows[0]))] if table_rows and table_rows[0] else []

        def render(row: list[str]) -> str:
            return " | ".join(str(value).ljust(widths[index]) for index, value in enumerate(row))

        lines = [render(list(map(str, table_rows[0]))), "-+-".join("-" * width for width in widths)]
        lines.extend(render(list(map(str, row))) for row in table_rows[1:])
        return "\n".join(lines)

tabulate = _tabulate
