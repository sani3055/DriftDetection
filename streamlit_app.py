"""Small, offline review demo. Run with: python -m streamlit run streamlit_app.py."""
from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.demo.review_data import (  # noqa: E402
    DIAGNOSIS_NAMES, SCENARIO_NAMES, SIGNALS, evaluate_example, load_review_data,
)


def signal_chart(example, thresholds, examples):
    """Each signal has a fixed scale across runs, with its decision limit marked."""
    charts = []
    for score_key, threshold_key, label in SIGNALS:
        score = getattr(example, score_key)
        limit = thresholds[threshold_key]
        maximum = max(limit, *(getattr(item, score_key) for item in examples)) * 1.10
        status = "Above limit" if score >= limit else "Below limit"
        frame = pd.DataFrame([{"Score": score, "Limit": limit, "Maximum": maximum, "Signal": label}])
        x = alt.X("Score:Q", scale=alt.Scale(domain=[0, maximum]), axis=None)
        track = alt.Chart(frame).mark_bar(color="#e5e7eb", size=16).encode(x=alt.X("Maximum:Q", scale=alt.Scale(domain=[0, maximum]), axis=None))
        bar = alt.Chart(frame).mark_bar(color="#2563eb", opacity=1 if score >= limit else 0.45, size=16).encode(
            x=x, tooltip=[alt.Tooltip("Signal:N"), alt.Tooltip("Score:Q", format=".4f"), alt.Tooltip("Limit:Q", format=".4f")],
        )
        marker = alt.Chart(frame).mark_rule(color="#111827", strokeWidth=2).encode(x=alt.X("Limit:Q", scale=alt.Scale(domain=[0, maximum]), axis=None))
        charts.append((track + bar + marker).properties(
            height=28,
            title=alt.TitleParams(text=label, subtitle=f"{status}   ·   Score {score:.3f}   ·   Limit {limit:.3f}", anchor="start", fontSize=15, subtitleFontSize=12, offset=10),
        ))
    return alt.vconcat(*charts, spacing=26).resolve_scale(x="independent").configure_view(stroke=None)


def main():
    st.set_page_config(page_title="CloudTrail Drift Demo", page_icon="🔎", layout="centered")
    st.caption("CAPSTONE REVIEW · SANIDHYA BHANDARI · 23BCT0029")
    st.title("CloudTrail Drift Diagnosis")
    st.write("See how data changes and SHAP explanations guide a model-update decision.")
    st.caption("Saved controlled experiments. No live AWS connection, training or changes to research outputs.")
    try:
        examples, thresholds = load_review_data(ROOT)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"The saved experiment evidence could not be loaded: {exc}")
        st.stop()

    seeds = sorted({item.seed for item in examples})
    with st.sidebar:
        st.header("Review demo")
        seed = st.selectbox("Held-out test run", seeds, key="seed")
        st.caption("The run number changes the saved sampling seed. These are controlled tests, not real incidents.")
        st.markdown("**Suggested sequence**\n\nStable activity → routine region change → simulated defence change → privilege change (missed case).")
        st.divider()
        st.write("**How it works**")
        st.write("1. Read saved drift signals.\n2. Run the actual diagnosis rule.\n3. Show whether the policy requests an update.")
        st.caption("Selecting a scenario recomputes the diagnosis only. It does not rerun the detector or SHAP.")

    available = {item.scenario for item in examples if item.seed == seed}
    scenarios = [key for key in SCENARIO_NAMES if key in available]
    scenario = st.selectbox("Test scenario", scenarios, format_func=SCENARIO_NAMES.__getitem__, key="scenario")
    example = next(item for item in examples if item.seed == seed and item.scenario == scenario)
    result = evaluate_example(example, thresholds)
    st.altair_chart(signal_chart(example, thresholds, examples), width="stretch")
    st.caption("Black marker = decision limit. Each signal uses its own scale, fixed across examples.")
    st.divider()
    left, right = st.columns([2, 1])
    left.subheader(DIAGNOSIS_NAMES[result.diagnosis])
    right.markdown("**Update requested**" if result.update_requested else "**No update requested**")
    st.write(result.reason)
    if result.matches_target:
        st.caption("The diagnosis matches this controlled scenario's known category.")
    elif example.expected_class == "security_relevant_drift":
        st.error("Missed security-related scenario: the diagnosis did not identify this as security-relevant drift.")
    else:
        st.warning("The diagnosis differs from this controlled scenario's known category.")
    st.caption("Known scenario labels are used only to evaluate the result. An update request does not confirm an attack.")

    with st.expander("Explain this example during the review"):
        st.write(f"**Scenario:** {SCENARIO_NAMES[scenario]}")
        st.write(f"**What the system sees:** {result.reason}")
        st.write("**Decision:** " + ("The coupling policy requests an update." if result.update_requested else "The coupling policy does not request an update."))
        if not result.matches_target:
            st.write("**Limitation:** This is a known test case the method did not classify correctly. It shows why an update decision is not a guarantee of detection.")

    with st.expander("What we learned from the experiments"):
        st.markdown(
            "- Combining data and SHAP drift reduced false alarms against the static policy in controlled tests.\n"
            "- We did not establish an overall detection improvement. Coupling matched simpler rules in the policy comparison.\n"
            "- Other detectors traded higher simulated-security recall for more benign false alarms. Larger samples did not always help.\n"
            "- On separate cloud logs, the original coupling threshold missed many security windows.\n"
            "- Recalibration worked better on that same target batch, but future unseen data still needs testing."
        )

    with st.expander("Scores and source evidence"):
        scores = pd.DataFrame([
            {"Signal": label, "Score": getattr(example, key), "Decision limit": thresholds[tkey], "Above limit": getattr(example, key) >= thresholds[tkey]}
            for key, tkey, label in SIGNALS
        ])
        st.dataframe(scores, hide_index=True, width="stretch")
        st.write(f"Recomputed decision agrees with the saved diagnosis and update request. Test seed: {seed}.")
        st.caption("Thresholds were selected on validation examples, not on the displayed held-out test run.")
        for name in ["diagnosis_results.csv", "diagnosis_thresholds.json", "adaptation_results.csv"]:
            st.code(f"data/benchmark/{name}")
        payload={"mode":"saved held-out experiment replay","example":asdict(example),"decision":asdict(result),"thresholds":thresholds}
        st.download_button("Download this example", json.dumps(payload, indent=2), file_name=f"{scenario}_seed_{seed}.json", mime="application/json")

    with st.expander("Real monthly observations"):
        st.caption("The original monthly corpus has no attack labels. This plot shows observed drift, not verified attacks.")
        figure=ROOT / "figures/monthly_drift_signals.png"
        if figure.is_file():
            st.image(str(figure), width="stretch")
        else:
            st.info("The optional monthly drift plot is not available in this checkout.")


if __name__ == "__main__":
    main()
