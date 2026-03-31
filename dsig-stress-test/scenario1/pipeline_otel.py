"""
pipeline_otel.py — Pipeline 1: OpenTelemetry + OpenMetrics simulation.

Receives the raw DataFrame (same input as all other pipelines).
Produces:
  - Aggregated metrics per node per time window (p50, p99, avg, error_rate).
  - OpenMetrics-formatted text output.
  - Silence handling: last-value carry-forward + stale=true flag after 2 missed cycles.

Output format per signal:
{
  "pipeline": "otel",
  "timestamp": "...",
  "node_id": "...",
  "perspective": "...",
  "metrics": { latency_p50, latency_p99, cpu_avg, memory_avg, error_rate },
  "openmetrics_text": "...",
  "stale": bool,
  "stale_since": str|null,
  "input_bytes": int,
  "output_bytes": int
}
"""

import json
import time as _time
from datetime import timezone

import numpy as np
import pandas as pd

PIPELINE_NAME = "otel"
WINDOW_MINUTES = 5   # rolling aggregation window
STALE_CYCLES   = 2   # consecutive missing cycles before stale=true


def _percentile(arr, p):
    valid = arr.dropna()
    if len(valid) == 0:
        return np.nan
    return float(np.percentile(valid, p))


def _compute_window_metrics(window_df):
    """Aggregate a 5-min window into OTel metric snapshot."""
    lat  = window_df["network_latency_ms"]
    cpu  = window_df["cpu_usage"]
    mem  = window_df["memory_usage"]
    up   = window_df["uptime_seconds"]

    # error_rate: fraction of rows where uptime == 0 (service down)
    error_rate = float((up == 0).sum() / max(len(up), 1) * 100)

    return {
        "latency_p50": _percentile(lat, 50),
        "latency_p99": _percentile(lat, 99),
        "cpu_avg":     float(cpu.mean()) if cpu.notna().any() else np.nan,
        "memory_avg":  float(mem.mean()) if mem.notna().any() else np.nan,
        "error_rate":  error_rate,
    }


def _to_openmetrics(metrics, node_id, ts_epoch):
    """Format metrics as OpenMetrics text."""
    lines = []
    label = f'node="{node_id}"'
    for key, val in metrics.items():
        if val is None or (isinstance(val, float) and np.isnan(val)):
            val_str = "NaN"
        else:
            val_str = f"{val:.4f}"
        lines.append(f"node_{key}{{{label}}} {val_str} {int(ts_epoch)}")
    return "\n".join(lines)


def run(df: pd.DataFrame) -> list[dict]:
    """
    Process the full 24h dataframe.
    Returns one signal dict per (node, time window).
    """
    signals = []
    nodes = df["node_id"].unique()

    for node_id in sorted(nodes):
        node_df = df[df["node_id"] == node_id].copy()
        node_df = node_df.sort_values("timestamp").reset_index(drop=True)

        perspective = node_df["perspective"].iloc[0]

        # Resample into WINDOW_MINUTES buckets
        node_df = node_df.set_index("timestamp")
        # Count NaN rows per window to detect silence
        all_nan_per_min = node_df["network_latency_ms"].isna()

        windows = node_df.resample(f"{WINDOW_MINUTES}min")

        last_known = None
        missed_cycles = 0

        for ts, window in windows:
            ts_str = ts.isoformat()
            ts_epoch = ts.timestamp()

            # Detect total silence (all rows are NaN in this window)
            all_silent = window["network_latency_ms"].isna().all()

            if all_silent:
                missed_cycles += 1
                stale = missed_cycles >= STALE_CYCLES
                stale_since = ts_str if stale and missed_cycles == STALE_CYCLES else (
                    last_known["stale_since"] if last_known and last_known.get("stale") else None
                )
                # Carry forward last known metrics
                metrics = last_known["metrics"] if last_known else {
                    "latency_p50": np.nan, "latency_p99": np.nan,
                    "cpu_avg": np.nan, "memory_avg": np.nan, "error_rate": np.nan
                }
            else:
                missed_cycles = 0
                stale = False
                stale_since = None
                metrics = _compute_window_metrics(window)

            # Annotate stale in metrics dict (for OTel text representation)
            metrics_with_stale = dict(metrics)

            otel_text = _to_openmetrics(metrics_with_stale, node_id, ts_epoch)
            if stale:
                otel_text += f'\nnode_stale{{node="{node_id}"}} 1 {int(ts_epoch)}'

            # Signal for LLM and metrics evaluation: the 5 key metrics as flat text
            signal_for_llm = (
                f"Pipeline: OpenTelemetry | Node: {node_id} | Time: {ts_str}\n"
                f"latency_p50={metrics.get('latency_p50', 'N/A'):.1f}ms  "
                f"latency_p99={metrics.get('latency_p99', 'N/A'):.1f}ms  "
                f"cpu_avg={metrics.get('cpu_avg', 'N/A'):.1f}%  "
                f"memory_avg={metrics.get('memory_avg', 'N/A'):.1f}%  "
                f"error_rate={metrics.get('error_rate', 'N/A'):.1f}%"
                + (f"  [STALE since {stale_since}]" if stale else "")
            ) if not any(
                v is None or (isinstance(v, float) and np.isnan(v))
                for v in [metrics.get("latency_p50"), metrics.get("latency_p99"),
                          metrics.get("cpu_avg"), metrics.get("memory_avg")]
            ) else (
                f"Pipeline: OpenTelemetry | Node: {node_id} | Time: {ts_str}\n"
                f"[ALL METRICS UNAVAILABLE — STALE since {stale_since}]"
            )

            input_bytes  = int(window.memory_usage(deep=True).sum())
            output_bytes = len(otel_text.encode("utf-8"))

            signal = {
                "pipeline":          PIPELINE_NAME,
                "timestamp":         ts_str,
                "node_id":           node_id,
                "perspective":       perspective,
                "metrics":           {k: (None if isinstance(v, float) and np.isnan(v) else v)
                                      for k, v in metrics.items()},
                "openmetrics_text":  otel_text,
                "signal_for_llm":    signal_for_llm,
                "stale":             stale,
                "stale_since":       stale_since,
                "input_bytes":       input_bytes,
                "output_bytes":      output_bytes,
            }
            last_known = signal
            signals.append(signal)

    return signals
