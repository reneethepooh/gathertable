"""Hand-written orchestrator: intake -> plan -> retrieve -> rank.

``run_pipeline`` returns every stage's output so the CLI can render them.
``plan_meal`` is the thin convenience wrapper for code that only wants the
final shortlist.
"""

from __future__ import annotations

from dataclasses import dataclass

from .agents.intake import run_intake
from .agents.planning import run_planning
from .agents.ranking import run_ranking
from .config import get_client
from .contracts import Candidate, DiningRequest, Recommendation, SearchPlan
from .tools.retrieval import MockProvider, Provider


@dataclass(frozen=True)
class PipelineResult:
    request: DiningRequest
    plan: SearchPlan
    candidates: list[Candidate]
    recommendations: list[Recommendation]


def run_pipeline(
    user_text: str,
    *,
    provider: Provider | None = None,
    client=None,
    top_n: int = 3,
    verbose: bool = False,
) -> PipelineResult:
    provider = provider if provider is not None else MockProvider()
    client = client if client is not None else get_client()

    log = _make_logger(verbose)

    log("Intake — parsing free text into DiningRequest")
    req = run_intake(user_text, client=client)
    log(req)

    log("Planning — producing SearchPlan")
    plan = run_planning(req, client=client)
    log(plan)

    log(f"Retrieval — searching with {type(provider).__name__}")
    candidates = provider.search(plan)
    log(f"  {len(candidates)} candidates returned")

    log(f"Ranking — top {top_n} with rationale")
    recs = run_ranking(req, plan, candidates, client=client, top_n=top_n)

    return PipelineResult(request=req, plan=plan, candidates=candidates, recommendations=recs)


def plan_meal(
    user_text: str,
    *,
    provider: Provider | None = None,
    client=None,
    top_n: int = 3,
    verbose: bool = False,
) -> list[Recommendation]:
    return run_pipeline(
        user_text,
        provider=provider,
        client=client,
        top_n=top_n,
        verbose=verbose,
    ).recommendations


def _make_logger(verbose: bool):
    if not verbose:
        return lambda _msg: None
    from rich import print as rprint

    def _log(msg):
        rprint(msg)

    return _log
