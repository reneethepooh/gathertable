"""Rich-formatted CLI demo.

    python -m gathertable "4 people, Union Square, $$, one vegetarian, lively"

The CLI loads ``.env`` automatically, runs the pipeline, and renders three
panels: the parsed request, the search plan, and the ranked shortlist.
"""

from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .contracts import DiningRequest, Recommendation, SearchPlan
from .orchestrator import run_pipeline
from .tools.retrieval import GooglePlacesProvider, MockProvider, Provider, YelpProvider

_PROVIDERS: dict[str, type[Provider]] = {
    "mock": MockProvider,
    "google": GooglePlacesProvider,
    "yelp": YelpProvider,
}


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    load_dotenv()
    console = Console()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        console.print("[red]ANTHROPIC_API_KEY is not set.[/red] Add it to .env and retry.")
        return 1

    if args.provider != "mock":
        console.print(
            f"[red]{args.provider!r} provider is a stub.[/red] "
            "Use [bold]--provider mock[/bold] for the MVP."
        )
        return 2
    provider = _PROVIDERS[args.provider]()

    result = run_pipeline(
        args.request,
        provider=provider,
        top_n=args.top_n,
        verbose=args.verbose,
    )

    _render_request(console, result.request)
    _render_plan(console, result.plan, candidate_count=len(result.candidates))
    _render_shortlist(console, result.recommendations)
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="gathertable",
        description="GatherTable — multi-agent group dining planner.",
    )
    parser.add_argument(
        "request",
        help='free-text dining request, e.g. "4 people, Union Square, $$, one vegetarian, lively"',
    )
    parser.add_argument(
        "--provider",
        choices=sorted(_PROVIDERS),
        default="mock",
        help="retrieval provider (default: mock; google/yelp are stubs).",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=3,
        help="how many ranked recommendations to return (default: 3).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="print intermediate stage outputs.",
    )
    return parser.parse_args(argv)


def _render_request(console: Console, req: DiningRequest) -> None:
    body = Text()
    body.append(f"party_size            : {req.party_size}\n")
    body.append(f"location              : {req.location}\n")
    body.append(f"budget                : {req.budget.value}\n")
    body.append(f"cuisines_wanted       : {_join(req.cuisines_wanted)}\n")
    body.append(f"dietary_restrictions  : {_join(req.dietary_restrictions)}\n")
    body.append(f"soft_preferences      : {_join(req.soft_preferences)}\n")
    if req.timing:
        body.append(f"timing                : {req.timing}\n")
    console.print(Panel(body, title="DiningRequest", border_style="cyan"))


def _render_plan(console: Console, plan: SearchPlan, *, candidate_count: int) -> None:
    body = Text()
    body.append("Hard filters (must_satisfy)\n", style="bold")
    for f in plan.must_satisfy or ["(none)"]:
        body.append(f"  - {f}\n")
    body.append("\nRanking criteria (weight)\n", style="bold")
    for c in plan.ranking_criteria or []:
        body.append(f"  - {c.name} ({c.weight:.2f})\n")
    if not plan.ranking_criteria:
        body.append("  (none)\n")
    body.append("\nConflict resolutions\n", style="bold")
    for r in plan.conflict_resolutions or ["(none)"]:
        body.append(f"  - {r}\n")
    body.append(f"\nRetrieval returned {candidate_count} candidate(s).\n", style="dim")
    console.print(Panel(body, title="SearchPlan", border_style="magenta"))


def _render_shortlist(console: Console, recs: list[Recommendation]) -> None:
    if not recs:
        console.print(Panel("No matches.", title="Shortlist", border_style="yellow"))
        return

    table = Table(title="Ranked shortlist", show_lines=False)
    table.add_column("#", justify="right", no_wrap=True)
    table.add_column("Name", style="bold")
    table.add_column("Cuisine")
    table.add_column("$", justify="center")
    table.add_column("Rating", justify="right")
    table.add_column("Dist", justify="right")
    table.add_column("Score", justify="right")
    for i, r in enumerate(recs, 1):
        c = r.candidate
        table.add_row(
            str(i),
            c.name,
            c.cuisine,
            c.price_level.value,
            f"{c.rating:.1f}",
            f"{c.distance_m} m",
            f"{r.score:.2f}",
        )
    console.print(table)

    for i, r in enumerate(recs, 1):
        body = Text()
        body.append(r.rationale + "\n")
        if r.constraints_satisfied:
            body.append("Satisfies: ", style="dim")
            body.append(", ".join(r.constraints_satisfied), style="dim")
        console.print(
            Panel(body, title=f"#{i}  {r.candidate.name}", border_style="green")
        )


def _join(items: list[str]) -> str:
    return ", ".join(items) if items else "(none)"


if __name__ == "__main__":
    sys.exit(main())
