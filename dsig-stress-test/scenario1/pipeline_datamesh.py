"""
pipeline_datamesh.py — Pipeline 2: Data Mesh / Data Product simulation.

Receives the same raw DataFrame as all other pipelines.
Produces a structured Data Product JSON per node per time window.

Silence handling:
  - stale: true when no data received for >= 2 cycles
  - last_updated preserved from last emission
  - stale_duration_minutes computed from last emission

Output format per signal:
{
  "pipeline": "datamesh",
  "data_product_id": "node-vitality-v1",
  "domain": "infrastructure",
  "version": "1.0",
  "timestamp": "...",
  "node_id": "...",
  "perspective": "...",
  "last_updated": "...",
  "quality_score": float,
  "kpis": { latency_p99_ms, cpu_avg_pct, memory_avg_pct, error_rate_pct, uptime_pct },
  "status": "NOMINAL" | "DEGRADED" | "CRITICAL",
  "last_known_values": {...},
  "stale": bool,
  "stale_duration_minutes": int|null,
  "signal_for_llm": str,
  "input_bytes": int,
  "output_bytes": int
}
"""

import json
import math

import numpy as np
import pandas as pd

PIPELINE_NAME  = "datamesh"
WINDOW_MINUTES = 5
STALE_CYCLES   = 2

# Status thresholds (based on p99 latency and error_rate)
CRITICAL_LATENCY_MS = 100
DEGRADED_LATENCY_MS = 30
CRITICAL_ERROR_PCT  = 10
DEGRADED_ERROR_PCT  = 1


def _compute_kpis(window: pd.DataFrame) -> dict:
    lat  = window["network_latency_ms"].dropna()
    cpu  = window["cpu_usage"].dropna()
    mem  = window["memory_usage"].dropna()
    up   = window["uptime_seconds"]

    p99     = float(np.percentile(lat, 99)) if len(lat) > 0 else math.nan
    cpu_avg = float(cpu.mean())             if len(cpu) > 0 else math.nan
    mem_avg = float(mem.mean())             if len(mem) > 0 else math.nan

    uptime_pct  = float((up > 0).sum() / max(len(up), 1) * 100)
    error_rate  = float((up == 0).sum() / max(len(up), 1) * 100)

    return {
        "latency_p99_ms":   round(p99, 2)     if not math.isnan(p99)     else None,
        "cpu_avg_pct":      round(cpu_avg, 2)  if not math.isnan(cpu_avg) else None,
        "memory_avg_pct":   round(mem_avg, 2)  if not math.isnan(mem_avg) else None,
        "error_rate_pct":   round(error_rate, 2),
        "uptime_pct":       round(uptime_pct, 2),
    }


def _quality_score(kpis: dict) -> float:
    """
    Simple data quality score (0–1): fraction of non-null KPIs,
    penalised by error_rate.
    """
    non_null = sum(1 for v in kpis.values() if v is not None)
    completeness = non_null / len(kpis)
    error_penalty = (kpis["error_rate_pct"] or 0) / 100
    return round(max(0.0, completeness - error_penalty), 4)


def _derive_status(kpis: dict, stale: bool) -> str:
    """Classify node status from KPIs (no access to ground truth at this stage)."""
    if stale:
        return "STALE"
    lat  = kpis.get("latency_p99_ms")
    err  = kpis.get("error_rate_pct", 0) or 0
    up   = kpis.get("uptime_pct", 100) or 100

    if (lat is not None and lat >= CRITICAL_LATENCY_MS) or err >= CRITICAL_ERROR_PCT or up < 50:
        return "CRITICAL"
    if (lat is not None and lat >= DEGRADED_LATENCY_MS) or err >= DEGRADED_ERROR_PCT:
        return "DEGRADED"
    return "NOMINAL"


def run(df: pd.DataFrame) -> list[dict]:
    signals = []
    nodes = df["node_id"].unique()

    for node_id in sorted(nodes):
        node_df = df[df["node_id"] == node_id].copy()
        node_df = node_df.sort_values("timestamp").set_index("timestamp")

        perspective = node_df["perspective"].iloc[0]

        windows       = node_df.resample(f"{WINDOW_MINUTES}min")
        last_known    = None
        missed_cycles = 0
        last_updated  = None

        for ts, window in windows:
            ts_str = ts.isoformat()
            all_silent = window["network_latency_ms"].isna().all()

            if all_silent:
                missed_cycles += 1
                stale = missed_cycles >= STALE_CYCLES
                stale_duration = (
                    (missed_cycles - STALE_CYCLES + 1) * WINDOW_MINUTES if stale else 0
                )
                kpis = last_known["kpis"] if last_known else {
                    "latency_p99_ms": None, "cpu_avg_pct": None,
                    "memory_avg_pct": None, "error_rate_pct": 0, "uptime_pct": 0
                }
                lu = last_updated or ts_str
            else:
                missed_cycles   = 0
                stale           = False
                stale_duration  = 0
                kpis            = _compute_kpis(window)
                lu              = ts_str
                last_updated    = ts_str

            quality = _quality_score(kpis)
            status  = _derive_status(kpis, stale)

            product = {
                "data_product_id":         "node-vitality-v1",
                "domain":                  "infrastructure",
                "version":                 "1.0",
                "last_updated":            lu,
                "quality_score":           quality,
                "kpis":                    kpis,
                "status":                  status,
                "last_known_values":       kpis,  # carry-forward = same dict
                "stale":                   stale,
                "stale_duration_minutes":  stale_duration if stale else None,
            }

            product_json = json.dumps(product, indent=2)

            # Signal text for LLM evaluation
            if not stale:
                signal_for_llm = (
                    f"Pipeline: DataMesh Data Product | Node: {node_id} | Time: {ts_str}\n"
                    f"status={status}  quality={quality:.2f}\n"
                    f"latency_p99={kpis.get('latency_p99_ms')}ms  "
                    f"cpu={kpis.get('cpu_avg_pct')}%  "
                    f"memory={kpis.get('memory_avg_pct')}%  "
                    f"error_rate={kpis.get('error_rate_pct')}%  "
                    f"uptime={kpis.get('uptime_pct')}%"
                )
            else:
                signal_for_llm = (
                    f"Pipeline: DataMesh Data Product | Node: {node_id} | Time: {ts_str}\n"
                    f"[STALE — last_updated={lu}, stale_duration={stale_duration}min]\n"
                    f"Last known: latency_p99={kpis.get('latency_p99_ms')}ms  "
                    f"cpu={kpis.get('cpu_avg_pct')}%  status=STALE"
                )

            input_bytes  = int(window.memory_usage(deep=True).sum())
            output_bytes = len(product_json.encode("utf-8"))

            signal = {
                "pipeline":                PIPELINE_NAME,
                "timestamp":               ts_str,
                "node_id":                 node_id,
                "perspective":             perspective,
                "signal_for_llm":          signal_for_llm,
                "input_bytes":             input_bytes,
                "output_bytes":            output_bytes,
                **product,
            }
            last_known = signal
            signals.append(signal)

    return signals
