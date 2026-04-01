"""
pipeline_otel_dsig.py — Pipeline 4: OTel → D-SIG hybrid (last-mile distillation).

This is the central thesis pipeline: OpenTelemetry acts as the collection/aggregation
layer, and D-SIG acts as the final distillation format for human/AI consumption.

Stages:
  1. Produce OTel metrics (identical to Pipeline 1).
  2. Consume those OTel metrics as input to D-SIG distillation.
  3. Output: D-SIG signal (same schema as Pipeline 3).

Logged separately:
  - otel_output_bytes: size of the OTel intermediate representation
  - dsig_output_bytes: size of the final D-SIG signal
  - total_pipeline_bytes: sum of both (chain cost)
  - input_bytes: size of raw data input

This tests the proposition that D-SIG is not a competitor to OTel but a
composable last-mile format layered on top of it.
"""

import json
import math
import re

import numpy as np
import pandas as pd

import pipeline_otel as otel
import pipeline_dsig as dsig

PIPELINE_NAME = "otel_dsig"


def _otel_to_dsig_row(otel_signal: dict) -> dict:
    """
    Translate OTel metric snapshot into a D-SIG input row.
    Maps:
      latency_p99_ms → network_latency_ms (primary latency signal)
      cpu_avg        → cpu_usage
      memory_avg     → memory_usage
      error_rate     → uptime_seconds proxy (error_rate > 0 → uptime = 0)
      disk_io        → not in OTel output → None (dns dimension gets half-credit)
    """
    metrics = otel_signal.get("metrics") or {}

    # Derive uptime proxy: if error_rate > 50%, treat as service down
    error_rate  = metrics.get("error_rate") or 0.0
    uptime_proxy = 0.0 if error_rate > 50.0 else 3600.0  # non-zero = alive

    return {
        "timestamp":          otel_signal["timestamp"],
        "node_id":            otel_signal["node_id"],
        "perspective":        otel_signal["perspective"],
        "network_latency_ms": metrics.get("latency_p99"),  # use p99 for D-SIG (conservative)
        "cpu_usage":          metrics.get("cpu_avg"),
        "memory_usage":       metrics.get("memory_avg"),
        "disk_io":            None,   # not in OTel output
        "uptime_seconds":     uptime_proxy,
        "stale":              otel_signal.get("stale", False),
    }


def run(df: pd.DataFrame) -> list[dict]:
    """
    Stage 1: run OTel pipeline to get aggregated metrics.
    Stage 2: distil each OTel signal through D-SIG.
    """
    # Stage 1 — OTel
    otel_signals = otel.run(df)

    # Group OTel signals by node for sequential processing
    from collections import defaultdict
    by_node: dict[str, list] = defaultdict(list)
    for sig in otel_signals:
        by_node[sig["node_id"]].append(sig)

    # Shared across all nodes so cross-node divergence can be computed (Rule 9)
    window_scores_shared: dict = {}   # ts_str → {node_id: score}
    node_bc: dict = {}               # node_id → baseline_cycle counter

    signals = []
    for node_id, node_otel_sigs in sorted(by_node.items()):
        prev_scores    = []
        baseline       = {"cpu": None, "mem": None}
        node_bc[node_id] = 0

        for otel_sig in node_otel_sigs:
            ts_str  = otel_sig["timestamp"]
            otel_bytes = len(json.dumps(otel_sig).encode("utf-8"))

            # Translate OTel snapshot → D-SIG input row
            row = _otel_to_dsig_row(otel_sig)

            # Update baseline from OTel cpu/memory (same EMA as pure D-SIG)
            alpha = 0.1
            if row["cpu_usage"] is not None and not math.isnan(float(row["cpu_usage"])):
                baseline["cpu"] = (row["cpu_usage"] if baseline["cpu"] is None
                                   else alpha * row["cpu_usage"] + (1 - alpha) * baseline["cpu"])
            if row["memory_usage"] is not None and not math.isnan(float(row["memory_usage"])):
                baseline["mem"] = (row["memory_usage"] if baseline["mem"] is None
                                   else alpha * row["memory_usage"] + (1 - alpha) * baseline["mem"])

            # Stage 2 — D-SIG distillation
            # CRITICAL CAP v0.5 — DeepSeek correction (applied inside compute_dsig_signal)
            sig = dsig.compute_dsig_signal(row, prev_scores, baseline, node_bc[node_id])

            # Track cross-node scores for baseline_cycles (shared across nodes)
            if ts_str not in window_scores_shared:
                window_scores_shared[ts_str] = {}
            window_scores_shared[ts_str][node_id] = sig["score"]

            # Signal text for LLM
            if sig["stale"]:
                signal_for_llm = (
                    f"Pipeline: OTel→D-SIG hybrid | Node: {node_id} "
                    f"({otel_sig['perspective']}) | Time: {ts_str}\n"
                    f"[STALE — OTel source went silent] "
                    f"Last score={sig['score']} label={sig['label']} trend={sig['trend']}"
                )
            else:
                dims = sig.get("dimensions", {})
                signal_for_llm = (
                    f"Pipeline: OTel→D-SIG hybrid | Node: {node_id} "
                    f"({otel_sig['perspective']}) | Time: {ts_str}\n"
                    f"score={sig['score']} label={sig['label']} color={sig['color']} "
                    f"trend={sig['trend']} baseline_cycles={sig['baseline_cycles']}\n"
                    f"[OTel source: latency_p99={otel_sig['metrics'].get('latency_p99')}ms "
                    f"cpu={otel_sig['metrics'].get('cpu_avg')}% "
                    f"error_rate={otel_sig['metrics'].get('error_rate')}%]"
                )

            dsig_bytes   = len(json.dumps(sig).encode("utf-8"))
            input_bytes  = otel_sig["input_bytes"]

            prev_scores.append(sig["score"])
            if len(prev_scores) > 10:
                prev_scores.pop(0)

            signals.append({
                "pipeline":           PIPELINE_NAME,
                "signal_for_llm":     signal_for_llm,
                "input_bytes":        input_bytes,
                "otel_output_bytes":  otel_bytes,
                "dsig_output_bytes":  dsig_bytes,
                "output_bytes":       dsig_bytes,   # final output = D-SIG signal
                "total_pipeline_bytes": otel_bytes + dsig_bytes,
                **sig,
            })

    # Post-processing: recompute baseline_cycles using complete shared window_scores (Rule 9)
    # Required because per-node loop processes all hub windows before local/oracle.
    _ts_to_sigs: dict = {}
    for _sig in signals:
        _ts_to_sigs.setdefault(_sig["timestamp"], []).append(_sig)

    for _ts in sorted(_ts_to_sigs.keys()):
        _all_scores = window_scores_shared.get(_ts, {})
        if len(_all_scores) >= 2:
            _vals    = list(_all_scores.values())
            _max_div = max(_vals) - min(_vals)
            for _sig in _ts_to_sigs[_ts]:
                _nid = _sig["source_id"]
                if _max_div <= 30:
                    node_bc[_nid] += 1
                else:
                    node_bc[_nid] = 0
                _sig["baseline_cycles"] = node_bc[_nid]
                if "signal_for_llm" in _sig:
                    _sig["signal_for_llm"] = re.sub(
                        r"baseline_cycles=\d+",
                        f"baseline_cycles={node_bc[_nid]}",
                        _sig["signal_for_llm"],
                    )

    return signals
