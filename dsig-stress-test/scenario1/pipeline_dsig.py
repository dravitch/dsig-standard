"""
pipeline_dsig.py — Pipeline 3: D-SIG v0.5 strict implementation.

Profile: IT-Node (NetPulse reference profile from SPEC.MD).

Dimension weights / max points:
  vital:       PRECONDITION — if failed, score capped at ≤ 20 (Rule 11)
  local:       10 pts  (gradual — network latency quality)
  internet:    25 pts  (binary — packet-loss proxy via latency spike)
  dns:         15 pts  (binary — disk I/O as DNS-proxy in this dataset)
  throughput:  35 pts  (gradual — rolling baseline comparison)
  hub:         15 pts  (semi-binary — hub scrape age)

Total max without precondition cap: 100 pts.

Rules enforced:
  Rule 1  — Fail-fast: vital=0 → raw_score collapsed
  Rule 8  — STALE: TTL exceeded → stale flag + trend CRITICAL_FALL
  Rule 10 — label = f(score) only; trend = f(d(score)/dt) only (independent)
  Rule 11 — Precondition: vital fails → score capped at ≤ 20

baseline_cycles (Rule 9, v0.5):
  Receiver-computed. Increments when all perspectives converge within 30 pts.
  Resets when divergence > 30 pts between any two perspectives.
  Stored per-node in the aggregator state dict passed in.
"""

import json
import math
from datetime import timezone

import numpy as np
import pandas as pd

PIPELINE_NAME  = "dsig"
WINDOW_MINUTES = 5   # same window as other pipelines
TTL_SECONDS    = 300 # 5 min — matches window

# Score → Label → Color (Rule 10, SPEC.MD Table)
SCORE_BANDS = [
    (85, 100, "EXCELLENT", "GREEN"),
    (60,  84, "GOOD",      "YELLOW"),
    (35,  59, "DEGRADED",  "ORANGE"),
    (0,   34, "CRITICAL",  "RED"),
]


def score_to_label_color(score: int) -> tuple[str, str]:
    for lo, hi, label, color in SCORE_BANDS:
        if lo <= score <= hi:
            return label, color
    return "CRITICAL", "RED"


def compute_trend(prev_scores: list[int], current: int) -> str:
    """
    Rule 10: trend = f(d(score)/dt).
    Uses last 3 scores to smooth noise.
    """
    if len(prev_scores) < 2:
        return "STABLE"
    recent = prev_scores[-3:] + [current]
    delta  = recent[-1] - recent[0]   # net change over window

    if delta >= 10:
        return "IMPROVING"
    if delta <= -25:
        return "CRITICAL_FALL"
    if delta <= -5:
        return "DEGRADING"
    return "STABLE"


# ---------------------------------------------------------------------------
# Dimension scoring functions (IT-Node profile)
# ---------------------------------------------------------------------------

def score_vital(uptime_seconds) -> int:
    """Precondition: 1 if service running, 0 if not."""
    if uptime_seconds is None or math.isnan(float(uptime_seconds)):
        return 1   # unknown ≠ dead; handled by TTL/STALE
    return 1 if float(uptime_seconds) > 0 else 0


def score_local(latency_ms) -> float:
    """
    Local dimension — gradual, 0–10 pts.
    Excellent: < 5ms → 10 pts
    Good: 5–20ms → linear 8–5 pts
    Degraded: 20–50ms → linear 5–2 pts
    Critical: > 100ms → 0 pts
    """
    if latency_ms is None or math.isnan(float(latency_ms)):
        return 5.0  # neutral when unknown
    lat = float(latency_ms)
    if lat < 5:
        return 10.0
    if lat < 20:
        return 10.0 - (lat - 5) / 15 * 3   # 10 → 7
    if lat < 50:
        return 7.0  - (lat - 20) / 30 * 5  # 7 → 2
    if lat < 100:
        return 2.0  - (lat - 50) / 50 * 2  # 2 → 0
    return 0.0


def score_internet(latency_ms) -> float:
    """
    Internet dimension — binary proxy, 0 or 25 pts.
    A very high latency spike (>= 100ms) on the EXTERNAL node is treated
    as internet degradation.
    """
    if latency_ms is None or math.isnan(float(latency_ms)):
        return 12.5   # half-credit when unknown
    return 0.0 if float(latency_ms) >= 100 else 25.0


def score_dns(disk_io) -> float:
    """
    DNS dimension — binary proxy via disk I/O (dataset has no DNS column).
    Assumption: disk I/O = 0 indicates system is unresponsive (DNS-equivalent failure).
    0 or 15 pts.
    """
    if disk_io is None or math.isnan(float(disk_io)):
        return 7.5   # half-credit when unknown
    return 0.0 if float(disk_io) == 0 else 15.0


def score_throughput(cpu_usage, mem_usage, baseline: dict) -> float:
    """
    Throughput dimension — gradual, 0–35 pts.
    Proxy: combined CPU + memory load vs baseline.
    High load → lower throughput score.
    baseline: {"cpu": float, "mem": float} — rolling averages.
    """
    if cpu_usage is None or math.isnan(float(cpu_usage)):
        return 17.5   # half-credit
    cpu = float(cpu_usage)
    mem = float(mem_usage) if (mem_usage is not None and not math.isnan(float(mem_usage))) else 50.0

    # Combined load index (0–100)
    load_index = cpu * 0.6 + mem * 0.4

    # Compare to baseline (if available)
    if baseline.get("cpu") and baseline.get("mem"):
        base_load = baseline["cpu"] * 0.6 + baseline["mem"] * 0.4
        deviation = (load_index - base_load) / max(base_load, 1)
        if deviation > 0.5:
            load_index = min(100, load_index * 1.2)  # penalise spikes vs baseline

    if load_index < 40:
        return 35.0
    if load_index < 60:
        return 35.0 - (load_index - 40) / 20 * 10  # 35 → 25
    if load_index < 80:
        return 25.0 - (load_index - 60) / 20 * 15  # 25 → 10
    if load_index < 95:
        return 10.0 - (load_index - 80) / 15 * 8   # 10 → 2
    return 0.0


def score_hub(latency_ms, scrape_age_seconds=None) -> float:
    """
    Hub dimension — semi-binary, 0–15 pts.
    Uses latency seen from CENTRAL perspective as hub health proxy.
    scrape_age_seconds: seconds since last hub scrape (optional).
    """
    if latency_ms is None or math.isnan(float(latency_ms)):
        if scrape_age_seconds and scrape_age_seconds > TTL_SECONDS:
            return 0.0
        return 7.5   # half-credit
    lat = float(latency_ms)
    if lat < 10:
        return 15.0
    if lat < 30:
        return 10.0
    if lat < 100:
        return 5.0
    return 0.0


# ---------------------------------------------------------------------------
# Main distillation
# ---------------------------------------------------------------------------

def compute_dsig_signal(row: dict, prev_scores: list[int],
                        baseline: dict, baseline_cycles: int) -> dict:
    """
    Produce one D-SIG signal from a single row/window aggregate.

    row keys: timestamp, node_id, perspective,
              cpu_usage, memory_usage, network_latency_ms,
              disk_io, process_count, uptime_seconds, stale
    """
    ts     = row["timestamp"]
    node   = row["node_id"]
    persp  = row["perspective"]
    stale  = row.get("stale", False)

    if stale:
        # Rule 8: TTL exceeded → STALE signal
        prev_label, prev_color = score_to_label_color(prev_scores[-1] if prev_scores else 50)
        return {
            "dsig_version":    "0.5",
            "score":           prev_scores[-1] if prev_scores else 50,
            "label":           prev_label,
            "color":           prev_color,
            "trend":           "CRITICAL_FALL",   # silence is always CRITICAL_FALL
            "timestamp":       ts,
            "ttl":             TTL_SECONDS,
            "source_id":       node,
            "perspective":     persp,
            "baseline_cycles": baseline_cycles,
            "stale":           True,
            "dimensions":      {},
            "flags":           ["STALE"],
        }

    # -- Dimension scores --
    vital_score = score_vital(row.get("uptime_seconds"))
    loc_score   = score_local(row.get("network_latency_ms"))
    int_score   = score_internet(row.get("network_latency_ms"))
    dns_s       = score_dns(row.get("disk_io"))
    thru_score  = score_throughput(row.get("cpu_usage"), row.get("memory_usage"), baseline)
    hub_s       = score_hub(row.get("network_latency_ms"))

    # -- Aggregation --
    raw_score = loc_score + int_score + dns_s + thru_score + hub_s  # max = 100

    # Rule 11: precondition gate — vital fails → cap at ≤ 20
    if vital_score == 0:
        raw_score = min(20, raw_score * 0.2)

    score = min(100, max(0, int(round(raw_score))))
    label, color = score_to_label_color(score)
    trend = compute_trend(prev_scores, score)

    return {
        "dsig_version":    "0.5",
        "score":           score,
        "label":           label,
        "color":           color,
        "trend":           trend,
        "timestamp":       ts,
        "ttl":             TTL_SECONDS,
        "source_id":       node,
        "perspective":     persp,
        "baseline_cycles": baseline_cycles,
        "stale":           False,
        "dimensions": {
            "vital":      {"score": vital_score * 100, "ts": ts, "ttl": TTL_SECONDS},
            "local":      {"score": round(loc_score * 10, 1),  "ts": ts, "ttl": 3600},
            "internet":   {"score": int_score,  "ts": ts, "ttl": 3600},
            "dns":        {"score": dns_s,       "ts": ts, "ttl": 3600},
            "throughput": {"score": round(thru_score, 1), "ts": ts, "ttl": 43200},
            "hub":        {"score": hub_s,       "ts": ts, "ttl": TTL_SECONDS * 2},
        },
        "flags": [],
    }


def _row_mean(series: pd.Series) -> float | None:
    valid = series.dropna()
    return float(valid.mean()) if len(valid) > 0 else None


def run(df: pd.DataFrame) -> list[dict]:
    signals       = []
    nodes         = df["node_id"].unique()
    # Aggregator state: baseline and baseline_cycles per node
    baselines     = {n: {"cpu": None, "mem": None} for n in nodes}
    b_cycles      = {n: 0 for n in nodes}
    prev_scores   = {n: [] for n in nodes}
    # All scores per window slot for cross-perspective divergence check
    window_scores = {}  # ts_str → {node_id: score}

    for node_id in sorted(nodes):
        node_df = df[df["node_id"] == node_id].copy()
        node_df = node_df.sort_values("timestamp").set_index("timestamp")

        perspective = node_df["perspective"].iloc[0]
        missed_cycles = 0

        windows = node_df.resample(f"{WINDOW_MINUTES}min")

        for ts, window in windows:
            ts_str    = ts.isoformat()
            all_silent = window["network_latency_ms"].isna().all()

            if ts_str not in window_scores:
                window_scores[ts_str] = {}

            if all_silent:
                missed_cycles += 1
                stale = missed_cycles >= 2
                agg_row = {
                    "timestamp":   ts_str,
                    "node_id":     node_id,
                    "perspective": perspective,
                    "stale":       stale,
                }
            else:
                missed_cycles = 0
                agg_row = {
                    "timestamp":          ts_str,
                    "node_id":            node_id,
                    "perspective":        perspective,
                    "cpu_usage":          _row_mean(window["cpu_usage"]),
                    "memory_usage":       _row_mean(window["memory_usage"]),
                    "network_latency_ms": _row_mean(window["network_latency_ms"]),
                    "disk_io":            _row_mean(window["disk_io"]),
                    "uptime_seconds":     _row_mean(window["uptime_seconds"]),
                    "stale":              False,
                }
                # Update rolling baseline (slow-moving 30-min EMA)
                alpha = 0.1
                bl = baselines[node_id]
                if agg_row["cpu_usage"] is not None:
                    bl["cpu"] = (agg_row["cpu_usage"] if bl["cpu"] is None
                                 else alpha * agg_row["cpu_usage"] + (1 - alpha) * bl["cpu"])
                if agg_row["memory_usage"] is not None:
                    bl["mem"] = (agg_row["memory_usage"] if bl["mem"] is None
                                 else alpha * agg_row["memory_usage"] + (1 - alpha) * bl["mem"])

            sig = compute_dsig_signal(
                agg_row, prev_scores[node_id],
                baselines[node_id], b_cycles[node_id]
            )

            window_scores[ts_str][node_id] = sig["score"]

            # Update baseline_cycles (Rule 9, receiver-computed):
            # Increment if all perspectives present at this ts diverge ≤ 30 pts.
            scores_at_ts = window_scores[ts_str]
            if len(scores_at_ts) >= 2:
                vals = list(scores_at_ts.values())
                max_div = max(vals) - min(vals)
                if max_div <= 30:
                    b_cycles[node_id] += 1
                else:
                    b_cycles[node_id] = 0   # divergence resets trust
                sig["baseline_cycles"] = b_cycles[node_id]

            # Signal text for LLM
            if sig["stale"]:
                signal_for_llm = (
                    f"Pipeline: D-SIG v0.5 | Node: {node_id} ({perspective}) | Time: {ts_str}\n"
                    f"[STALE — TTL exceeded] Last score={sig['score']} "
                    f"label={sig['label']} color={sig['color']} trend={sig['trend']}"
                )
            else:
                dims = sig.get("dimensions", {})
                signal_for_llm = (
                    f"Pipeline: D-SIG v0.5 | Node: {node_id} ({perspective}) | Time: {ts_str}\n"
                    f"score={sig['score']} label={sig['label']} color={sig['color']} "
                    f"trend={sig['trend']} baseline_cycles={sig['baseline_cycles']}\n"
                    f"vital={dims.get('vital',{}).get('score','?')}  "
                    f"local={dims.get('local',{}).get('score','?')}  "
                    f"internet={dims.get('internet',{}).get('score','?')}  "
                    f"dns={dims.get('dns',{}).get('score','?')}  "
                    f"throughput={dims.get('throughput',{}).get('score','?')}  "
                    f"hub={dims.get('hub',{}).get('score','?')}"
                )

            sig_json     = json.dumps(sig)
            input_bytes  = int(window.memory_usage(deep=True).sum())
            output_bytes = len(sig_json.encode("utf-8"))

            prev_scores[node_id].append(sig["score"])
            if len(prev_scores[node_id]) > 10:
                prev_scores[node_id].pop(0)

            signals.append({
                "pipeline":       PIPELINE_NAME,
                "signal_for_llm": signal_for_llm,
                "input_bytes":    input_bytes,
                "output_bytes":   output_bytes,
                **sig,
            })

    return signals
