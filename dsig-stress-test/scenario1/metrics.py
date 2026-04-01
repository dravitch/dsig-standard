"""
metrics.py — Compute the 10 standardised metrics for each pipeline × incident.

Metrics:
  M01  decision_latency_s         — measured externally by llm_eval.py; populated post-LLM call
  M02  signal_compactness_bytes   — len(json.dumps(signal))
  M03  noise_reduction_ratio_pct  — (input_bytes - output_bytes) / input_bytes * 100
  M04  silence_resilience         — {detection_score: 0-100, diagnostic_score: 0-100}
  M05  convergence_diagnostic_pct — % incidents where perspective divergence was detected
  M06  diagnostic_precision_pct   — % causes correctly identified vs ground_truth
  M07  interpretability_score     — LLM self-rating 1-10 (populated by llm_eval.py)
  M08  trust_accumulation_utility — % alertes pertinentes lors des ruptures baseline_cycles
  M09  false_alarm_rate_pct       — alerts raised without a real incident
  M10  implementation_effort_loc  — lines of code in the pipeline file

All functions receive the full list of pipeline signals + ground truth dict.
"""

import json
import math
import os
import re

PIPELINE_FILES = {
    "otel":      "pipeline_otel.py",
    "datamesh":  "pipeline_datamesh.py",
    "dsig":      "pipeline_dsig.py",
    "otel_dsig": "pipeline_otel_dsig.py",
}

SCENARIO_DIR = os.path.dirname(__file__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _signals_in_incident(signals: list[dict], incident: dict) -> list[dict]:
    """Return signals whose timestamp falls within [t_start_h, t_end_h]."""
    t_start = incident["t_start_h"] * 3600   # seconds since midnight = offset within 24h sim
    t_end   = incident["t_end_h"]   * 3600

    def _offset(sig):
        """Parse ISO timestamp and return seconds since simulation start (00:00 UTC)."""
        import pandas as pd
        ts = pd.Timestamp(sig["timestamp"])
        return ts.hour * 3600 + ts.minute * 60 + ts.second

    return [s for s in signals if t_start <= _offset(s) <= t_end]


def _is_alert_signal(sig: dict, pipeline: str) -> bool:
    """Return True if the signal constitutes an alert (anomaly detected)."""
    if pipeline == "otel":
        m = sig.get("metrics") or {}
        lat = m.get("latency_p99") or m.get("latency_p99_ms")
        err = m.get("error_rate") or 0
        stale = sig.get("stale", False)
        return stale or (lat is not None and lat >= 30) or err >= 1

    if pipeline == "datamesh":
        return sig.get("status") in ("DEGRADED", "CRITICAL", "STALE")

    if pipeline in ("dsig", "otel_dsig"):
        return sig.get("label") in ("DEGRADED", "CRITICAL") or sig.get("stale", False)

    return False


def _silence_detected(signals: list[dict], incident: dict, pipeline: str) -> bool:
    """Return True if the pipeline flagged silence during a silence-type incident."""
    inc_sigs = _signals_in_incident(signals, incident)
    if not inc_sigs:
        return False

    silent_src = incident.get("silent_source")
    if not silent_src:
        return False

    # Filter to the silent node's signals
    sigs_from_src = [s for s in inc_sigs if s.get("perspective") == silent_src]
    if not sigs_from_src:
        # No signals emitted → silence detected by absence
        return True

    for s in sigs_from_src:
        if s.get("stale") or s.get("status") == "STALE" or s.get("trend") == "CRITICAL_FALL":
            return True
    return False


def _cause_identified(signals: list[dict], incident: dict, pipeline: str) -> bool:
    """
    Heuristic: cause identified if:
    - Alert raised AND only the affected perspective's signals show abnormality
    - Other perspectives remain nominal during the same window.
    """
    inc_sigs = _signals_in_incident(signals, incident)
    if not inc_sigs:
        return False

    cause = incident["cause"]   # "LOCAL" | "CENTRAL" | "EXTERNAL"

    affected = [s for s in inc_sigs if s.get("perspective") == cause]
    others   = [s for s in inc_sigs if s.get("perspective") != cause]

    # Affected perspective must raise an alert
    affected_alerted = any(_is_alert_signal(s, pipeline) for s in affected)
    if not affected_alerted:
        return False

    # Other perspectives must NOT all raise alerts (isolation)
    if others:
        others_all_alerted = all(_is_alert_signal(s, pipeline) for s in others)
        return not others_all_alerted

    return True


# ---------------------------------------------------------------------------
# M02 — Signal Compactness
# ---------------------------------------------------------------------------

def m02_compactness(signals: list[dict]) -> float:
    """Average output_bytes across all signals."""
    sizes = [s.get("output_bytes", 0) for s in signals]
    return round(sum(sizes) / max(len(sizes), 1), 1)


# ---------------------------------------------------------------------------
# M03 — Noise Reduction Ratio
# ---------------------------------------------------------------------------

def m03_noise_reduction(signals: list[dict]) -> float:
    total_in  = sum(s.get("input_bytes",  0) for s in signals)
    total_out = sum(s.get("output_bytes", 0) for s in signals)
    if total_in == 0:
        return 0.0
    return round((total_in - total_out) / total_in * 100, 2)


# ---------------------------------------------------------------------------
# M04 — Silence Resilience (two sub-components per ANALYSIS_PROTOCOL)
# ---------------------------------------------------------------------------

def m04_silence_resilience(signals: list[dict], gt: dict, pipeline: str) -> dict:
    """
    detection_score (0-100): fraction of silence incidents where silence was flagged.
    diagnostic_score (0-100): fraction of silence incidents where cause was isolated.
    """
    silence_incidents = [i for i in gt["incidents"]
                         if i["type"] in ("silence_local", "silence_oracle")]
    if not silence_incidents:
        return {"detection_score": None, "diagnostic_score": None}

    detected  = 0
    diagnosed = 0
    for inc in silence_incidents:
        if _silence_detected(signals, inc, pipeline):
            detected += 1
        if _cause_identified(signals, inc, pipeline):
            diagnosed += 1

    n = len(silence_incidents)
    return {
        "detection_score":   round(detected  / n * 100, 1),
        "diagnostic_score":  round(diagnosed / n * 100, 1),
    }


# ---------------------------------------------------------------------------
# M05 — Convergence Diagnostic
# ---------------------------------------------------------------------------

def m05_convergence_diagnostic(signals: list[dict], gt: dict, pipeline: str) -> float:
    """% incidents where the correct perspective was identified as the cause."""
    total   = len(gt["incidents"])
    correct = sum(1 for inc in gt["incidents"] if _cause_identified(signals, inc, pipeline))
    return round(correct / max(total, 1) * 100, 1)


# ---------------------------------------------------------------------------
# M06 — Diagnostic Precision
# ---------------------------------------------------------------------------

def m06_diagnostic_precision(signals: list[dict], gt: dict, pipeline: str) -> float:
    """Same as M05 but strictly evaluating expected_diagnosis match (also heuristic)."""
    return m05_convergence_diagnostic(signals, gt, pipeline)


# ---------------------------------------------------------------------------
# M08 — Trust Accumulation Utility (D-SIG only; others get None)
# ---------------------------------------------------------------------------

def m08_trust_accumulation(signals: list[dict], gt: dict, pipeline: str) -> float | None:
    """
    For D-SIG pipelines: % of incidents detected shortly after a baseline_cycles reset.
    A reset indicates a sudden trust break — high utility if it coincides with a real incident.
    """
    if pipeline not in ("dsig", "otel_dsig"):
        return None

    # Find signals where baseline_cycles reset to 0 (after being > 0)
    resets = []
    prev_bc = None
    for sig in signals:
        bc = sig.get("baseline_cycles", 0)
        if prev_bc is not None and prev_bc > 5 and bc == 0:
            resets.append(sig["timestamp"])
        prev_bc = bc

    if not resets:
        return 0.0

    # Check how many resets align with a real incident (within ±10 min)
    import pandas as pd

    # SCENARIO2 ADAPTATION — derive sim_date from signals instead of hardcoding
    sim_date = (pd.Timestamp(signals[0]["timestamp"]).strftime("%Y-%m-%d")
                if signals else "2026-03-30")

    incident_ranges = []
    for inc in gt["incidents"]:
        t_s = pd.Timestamp(f"{sim_date}T{int(inc['t_start_h']):02d}:"
                           f"{int((inc['t_start_h'] % 1) * 60):02d}:00Z")
        t_e = pd.Timestamp(f"{sim_date}T{int(inc['t_end_h']):02d}:"
                           f"{int((inc['t_end_h'] % 1) * 60):02d}:00Z")
        incident_ranges.append((t_s - pd.Timedelta(minutes=10),
                                 t_e + pd.Timedelta(minutes=10)))

    useful = 0
    for reset_ts in resets:
        rt = pd.Timestamp(reset_ts)
        if any(lo <= rt <= hi for lo, hi in incident_ranges):
            useful += 1

    return round(useful / max(len(resets), 1) * 100, 1)


# ---------------------------------------------------------------------------
# M09 — False Alarm Rate
# ---------------------------------------------------------------------------

def m09_false_alarm_rate(signals: list[dict], gt: dict, pipeline: str) -> float:
    """
    % of alerts raised that do NOT correspond to a real incident.
    """
    import pandas as pd

    # SCENARIO2 ADAPTATION — derive sim_date from signals instead of hardcoding
    sim_date = (pd.Timestamp(signals[0]["timestamp"]).strftime("%Y-%m-%d")
                if signals else "2026-03-30")

    incident_ranges = []
    for inc in gt["incidents"]:
        t_s = pd.Timestamp(f"{sim_date}T{int(inc['t_start_h']):02d}:"
                           f"{int((inc['t_start_h'] % 1) * 60):02d}:00Z")
        t_e = pd.Timestamp(f"{sim_date}T{int(inc['t_end_h']):02d}:"
                           f"{int((inc['t_end_h'] % 1) * 60):02d}:00Z")
        # Give ±10 min tolerance around each incident
        incident_ranges.append((t_s - pd.Timedelta(minutes=10),
                                 t_e + pd.Timedelta(minutes=10)))

    alerts = [s for s in signals if _is_alert_signal(s, pipeline)]
    if not alerts:
        return 0.0

    false_alarms = 0
    for sig in alerts:
        ts = pd.Timestamp(sig["timestamp"])
        if not any(lo <= ts <= hi for lo, hi in incident_ranges):
            false_alarms += 1

    return round(false_alarms / len(alerts) * 100, 1)


# ---------------------------------------------------------------------------
# M10 — Implementation Effort (LOC)
# ---------------------------------------------------------------------------

def m10_loc(pipeline: str) -> int:
    fname = PIPELINE_FILES.get(pipeline)
    if not fname:
        return 0
    fpath = os.path.join(SCENARIO_DIR, fname)
    try:
        with open(fpath) as f:
            lines = f.readlines()
        # Count non-empty, non-comment-only lines
        return sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
    except FileNotFoundError:
        return 0


# ---------------------------------------------------------------------------
# Full metrics computation for one pipeline
# ---------------------------------------------------------------------------

def compute_all(pipeline: str, signals: list[dict], gt: dict,
                llm_results: list[dict] | None = None) -> dict:
    """
    Aggregate all 10 metrics for a given pipeline.
    llm_results: list of {pipeline, latency_s, interpretability_rating, ...}
    """
    # M01 — from LLM results
    if llm_results:
        llm_for_pipe = [r for r in llm_results if r["pipeline"] == pipeline]
        m01 = round(sum(r["latency_s"] for r in llm_for_pipe) / max(len(llm_for_pipe), 1), 3)
        m07 = round(sum(r.get("interpretability_rating") or 0
                        for r in llm_for_pipe) / max(len(llm_for_pipe), 1), 1)
    else:
        m01 = None
        m07 = None

    return {
        "pipeline":                    pipeline,
        "M01_decision_latency_s":      m01,
        "M02_signal_compactness_bytes": m02_compactness(signals),
        "M03_noise_reduction_ratio_pct": m03_noise_reduction(signals),
        "M04_silence_resilience":       m04_silence_resilience(signals, gt, pipeline),
        "M05_convergence_diagnostic_pct": m05_convergence_diagnostic(signals, gt, pipeline),
        "M06_diagnostic_precision_pct": m06_diagnostic_precision(signals, gt, pipeline),
        "M07_interpretability_score":   m07,
        "M08_trust_accumulation_utility": m08_trust_accumulation(signals, gt, pipeline),
        "M09_false_alarm_rate_pct":     m09_false_alarm_rate(signals, gt, pipeline),
        "M10_implementation_effort_loc": m10_loc(pipeline),
    }
