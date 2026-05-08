"""Rich table display for RegressionResult."""
from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.table import Table

from cachewatch.regression import RegressionResult

_console = Console()


def _fmt(value: Optional[float], decimals: int = 4, sign: bool = False) -> str:
    if value is None:
        return "N/A"
    fmt = f"{{:+.{decimals}f}}" if sign else f"{{:.{decimals}f}}"
    return fmt.format(value)


def build_regression_table(result: RegressionResult) -> Table:
    """Return a Rich Table summarising *result*."""
    table = Table(title="Polynomial Regression", show_header=True, header_style="bold cyan")
    table.add_column("Property", style="dim", min_width=20)
    table.add_column("Value")

    table.add_row("Degree", str(result.degree))
    table.add_row("Sample count", str(result.sample_count))
    table.add_row(
        "R\u00b2",
        _fmt(result.r_squared) if result.r_squared is not None else "N/A",
    )

    for i, coef in enumerate(result.coefficients):
        power = result.degree - i
        label = f"Coefficient (x^{power})" if power > 0 else "Intercept"
        table.add_row(label, _fmt(coef, decimals=6, sign=True))

    return table


def print_regression_table(result: RegressionResult) -> None:  # pragma: no cover
    """Print the regression table to stdout."""
    _console.print(build_regression_table(result))
