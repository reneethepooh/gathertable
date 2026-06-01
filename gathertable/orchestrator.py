"""Hand-written orchestrator: intake -> plan -> retrieve -> rank.

No framework. One client, one provider, four sequential calls.
"""

from __future__ import annotations

from .agents.intake import run_intake
from .agents.planning import run_planning
from .agents.ranking import run_ranking
from .config import get_client
from .contracts import Recommendation
from .tools.retrieval import MockProvider, Provider


def plan_meal(
    user_text: str,
    *,
    provider: Provider | None = None,
    client=None,
    top_n: int = 3,
    verbose: bool = False,
) -> list[Recommendation]:
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
    return recs


def _make_logger(verbose: bool):
    if not verbose:
        return lambda _msg: None
    from rich import print as rprint

    def _log(msg):
        rprint(msg)

    return _log
