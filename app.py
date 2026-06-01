"""GatherTable — Streamlit web frontend.

Run with:

    streamlit run app.py

Presentation only. Reuses ``gathertable.orchestrator.run_pipeline`` directly,
so any change to the four-agent pipeline shows up here for free.
"""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from gathertable.contracts import DiningRequest, Recommendation, SearchPlan
from gathertable.orchestrator import run_pipeline


load_dotenv(Path(__file__).parent / ".env")


st.set_page_config(page_title="GatherTable", layout="centered")

st.title("GatherTable")
st.caption(
    "A multi-agent group dining planner. Reconciles everyone's preferences "
    "into a short, justified shortlist."
)

query = st.text_input(
    "Your dining request",
    value="4 people, Union Square, $$, one vegetarian, lively",
    help="Free text — party size, location, budget, dietary needs, vibe.",
)
submitted = st.button("Find restaurants", type="primary")


def _or_none(items: list[str]) -> str:
    return ", ".join(items) if items else "_(none)_"


def _render_request(req: DiningRequest) -> None:
    with st.expander("Parsed request", expanded=True):
        left, right = st.columns(2)
        left.markdown(f"**Party size**\n\n{req.party_size}")
        right.markdown(f"**Location**\n\n{req.location}")
        left.markdown(f"**Budget**\n\n`{req.budget.value}`")
        right.markdown(f"**Cuisines wanted**\n\n{_or_none(req.cuisines_wanted)}")
        left.markdown(f"**Dietary**\n\n{_or_none(req.dietary_restrictions)}")
        right.markdown(f"**Soft preferences**\n\n{_or_none(req.soft_preferences)}")
        if req.timing:
            st.markdown(f"**Timing**: {req.timing}")


def _render_plan(plan: SearchPlan, *, candidate_count: int) -> None:
    st.subheader("Search plan")

    st.markdown("**Hard filters** (must_satisfy)")
    if plan.must_satisfy:
        st.markdown("\n".join(f"- `{f}`" for f in plan.must_satisfy))
    else:
        st.markdown("_(none)_")

    st.markdown("**Ranking criteria** (weight)")
    if plan.ranking_criteria:
        st.markdown(
            "\n".join(f"- {c.name} ({c.weight:.2f})" for c in plan.ranking_criteria)
        )
    else:
        st.markdown("_(none)_")

    st.markdown("**Conflict resolutions**")
    if plan.conflict_resolutions:
        st.markdown("\n".join(f"- {r}" for r in plan.conflict_resolutions))
    else:
        st.markdown("_(none)_")

    st.caption(f"Retrieval returned {candidate_count} candidate(s).")


def _render_shortlist(recs: list[Recommendation]) -> None:
    st.subheader("Ranked shortlist")
    if not recs:
        st.warning(
            "No matches. Try loosening the budget, location, or cuisine."
        )
        return
    for i, rec in enumerate(recs, 1):
        with st.container(border=True):
            st.markdown(f"### {i}. {rec.candidate.name}")
            c = rec.candidate
            cols = st.columns(5)
            cols[0].metric("Cuisine", c.cuisine)
            cols[1].metric("Price", c.price_level.value)
            cols[2].metric("Rating", f"{c.rating:.1f}")
            cols[3].metric("Distance", f"{c.distance_m} m")
            cols[4].metric("Score", f"{rec.score:.2f}")
            st.markdown(f"_{rec.rationale}_")
            if rec.constraints_satisfied:
                st.caption("Satisfies: " + ", ".join(rec.constraints_satisfied))


if submitted:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.error("ANTHROPIC_API_KEY is not set. Add it to .env and restart.")
        st.stop()
    if not query.strip():
        st.error("Please enter a request.")
        st.stop()

    try:
        with st.spinner("Thinking through the group's preferences…"):
            result = run_pipeline(query, top_n=3)
    except Exception as exc:
        st.error(f"Pipeline failed: {exc}")
        st.stop()

    _render_request(result.request)
    _render_plan(result.plan, candidate_count=len(result.candidates))
    _render_shortlist(result.recommendations)
