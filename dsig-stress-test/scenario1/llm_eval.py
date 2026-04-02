"""
llm_eval.py — LLM evaluation of pipeline signals via Anthropic API.

Fixed prompt (identical for all 4 pipelines):
  "Given this signal, what is the system status and recommended action
   in one sentence? Rate the clarity of this signal from 1 to 10."

Model: claude-sonnet-4-6
Max tokens: 150
Calls: 4 incidents × 4 pipelines = 16 calls

Logged per call:
  - pipeline
  - incident_id
  - input_tokens
  - output_tokens
  - latency_s
  - response (raw text)
  - interpretability_rating (extracted 1-10 from response)
"""

import os
import re
import time

import anthropic

# PROMPT UPDATED v4 — units, baseline_cycles semantics, critical threshold
PROMPT_FIXED = (
    "Given this signal, what is the system status and recommended action "
    "in one sentence? Rate the clarity of this signal on a scale of 1 to 10. "
    "Note: in this standard, 'label' indicates current state and 'trend' "
    "indicates momentum — they are independent. A label of GOOD with trend "
    "CRITICAL_FALL means the system is currently operational but deteriorating "
    "rapidly. This is intentional, not a contradiction. "
    "Dimension scores are on a 0-100 scale (higher is better); any dimension "
    "below 30 is considered critical. 'baseline_cycles' is a trust metric: "
    "higher means more cycles of stable multi-perspective convergence."
)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 150


def _extract_rating(text: str) -> float | None:
    """
    Extract a numeric rating 1-10 from LLM response.
    Looks for patterns like: "8/10", "clarity: 7", "8 out of 10", "rating: 9".
    """
    patterns = [
        r"\b([1-9]|10)\s*/\s*10\b",
        r"clarity[:\s]+([1-9]|10)\b",
        r"rating[:\s]+([1-9]|10)\b",
        r"\b([1-9]|10)\s+out\s+of\s+10\b",
        r"\b([1-9]|10)\s*[/\\]10\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return float(m.group(1))
    # Fallback: last standalone digit 1-9 in the text
    digits = re.findall(r"\b([1-9]|10)\b", text)
    if digits:
        return float(digits[-1])
    return None


def evaluate_signal(signal_text: str, pipeline_name: str,
                    incident_id: str, client: anthropic.Anthropic) -> dict:
    """
    Call the LLM with the fixed prompt and the pipeline signal text.
    Returns a result dict.
    """
    prompt = f"{PROMPT_FIXED}\n\nSignal:\n{signal_text}"

    start = time.perf_counter()
    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    latency = time.perf_counter() - start

    response_text = response.content[0].text if response.content else ""
    rating = _extract_rating(response_text)

    return {
        "pipeline":               pipeline_name,
        "incident_id":            incident_id,
        "input_tokens":           response.usage.input_tokens,
        "output_tokens":          response.usage.output_tokens,
        "input_tokens_to_llm":    response.usage.input_tokens,   # explicit per ANALYSIS_PROTOCOL
        "latency_s":              round(latency, 3),
        "response":               response_text,
        "interpretability_rating": rating,
    }


def run_all_evaluations(
    pipeline_signals: dict[str, list[dict]],
    gt: dict,
    api_key: str | None = None,
) -> list[dict]:
    """
    For each pipeline × incident: find the signal closest to the incident start,
    call the LLM, collect results.

    pipeline_signals: {"otel": [...], "datamesh": [...], ...}
    gt: ground_truth dict
    """
    import pandas as pd

    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY not set. Export it before running the stress test."
        )

    client  = anthropic.Anthropic(api_key=api_key)
    results = []

    # Derive sim_date from first available signal (supports multi-scenario reuse)
    all_sigs = [s for sigs in pipeline_signals.values() for s in sigs]
    sim_date = (pd.Timestamp(all_sigs[0]["timestamp"]).strftime("%Y-%m-%d")
                if all_sigs else "2026-03-30")

    for inc in gt["incidents"]:
        inc_id  = inc["id"]
        t_start = pd.Timestamp(
            f"{sim_date}T{int(inc['t_start_h']):02d}:"
            f"{int((inc['t_start_h'] % 1) * 60):02d}:00Z"
        )

        for pipeline_name, signals in pipeline_signals.items():
            # Find the signal closest to the incident start timestamp
            candidates = [
                s for s in signals
                if s.get("perspective") == inc.get("cause") or
                   s.get("node_id", "").startswith("node-")
            ]
            if not candidates:
                candidates = signals

            # Sort by temporal distance to incident start
            def _dist(s):
                try:
                    ts = pd.Timestamp(s["timestamp"])
                    return abs((ts - t_start).total_seconds())
                except Exception:
                    return float("inf")

            best = min(candidates, key=_dist)
            signal_text = best.get("signal_for_llm") or str(best)

            print(f"  [llm_eval] {pipeline_name} × {inc_id} ...", end=" ", flush=True)
            result = evaluate_signal(signal_text, pipeline_name, inc_id, client)
            print(f"latency={result['latency_s']}s  rating={result['interpretability_rating']}")
            results.append(result)

    return results
