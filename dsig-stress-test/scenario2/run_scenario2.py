"""
run_scenario2.py — Orchestrator for D-SIG Stress Test · Scenario 2.

Usage:
    python scenario2/run_scenario2.py [--synthetic] [--skip-llm]

    --synthetic   Force synthetic dataset generation (skip Kaggle attempt)
    --skip-llm    Skip LLM evaluation (useful for dry runs without API key)

Single command, no interactive input.

Steps:
    1. Load ground truth (scenario2/ground_truth_s2.json)
    2. Fetch / generate dataset (throughput + latency)
    3. Run all 4 pipelines on the same raw data (imported from scenario1/)
    4. For each pipeline × each incident: extract signal, call LLM
    5. Compute all 10 metrics per pipeline
    6. Write results/scenario2/
       - raw_outputs/*.json
       - metrics_report.json
       - llm_responses.json
       - summary.csv

Pipelines are imported from scenario1/ — not duplicated.
Column mapping is applied here before data reaches the pipelines.
"""

import csv
import json
import os
import sys
import time

import pandas as pd

# Import pipelines and shared modules from scenario1
SCENARIO1_DIR = os.path.join(os.path.dirname(__file__), "..", "scenario1")
sys.path.insert(0, SCENARIO1_DIR)

# Also add scenario2/data to path for fetch_data_s2
SCENARIO2_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(SCENARIO2_DIR, "data"))

import pipeline_otel
import pipeline_datamesh
import pipeline_dsig
import pipeline_otel_dsig
import metrics as metrics_mod
import llm_eval

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR      = os.path.dirname(SCENARIO2_DIR)
RESULTS_DIR   = os.environ.get("DSIG_RESULTS_DIR",
                    os.path.join(ROOT_DIR, "results", "scenario2"))
RAW_DIR       = os.path.join(RESULTS_DIR, "raw_outputs")
GT_PATH       = os.path.join(SCENARIO2_DIR, "ground_truth_s2.json")
DATA_CSV      = os.path.join(SCENARIO2_DIR, "data", "network_metrics.csv")

PIPELINE_NAMES = ["otel", "datamesh", "dsig", "otel_dsig"]

# Column mapping: S2 dataset → pipeline schema
# (pipeline_*.py expect the S2 column names used by fetch_data_s2 directly,
#  but this mapping handles any Kaggle variant that may differ)
COLUMN_MAPPING = {
    "latency":        "network_latency_ms",
    "response_time":  "network_latency_ms",
    "cpu":            "cpu_usage",
    "memory":         "memory_usage",
    "mem":            "memory_usage",
    "uptime":         "uptime_seconds",
    "io":             "disk_io",
    "throughput":     "throughput_mbps",
    "bandwidth":      "throughput_mbps",
    "server_id":      "node_id",
}


def _ensure_dirs():
    for d in [RESULTS_DIR, RAW_DIR]:
        os.makedirs(d, exist_ok=True)


def _load_ground_truth() -> dict:
    with open(GT_PATH) as f:
        return json.load(f)


def _load_data(force_synthetic: bool) -> tuple[pd.DataFrame, str]:
    """Return (dataframe, data_source_str)."""
    import fetch_data_s2
    if not os.path.exists(DATA_CSV):
        csv_path, data_source = fetch_data_s2.fetch(force_synthetic=force_synthetic)
    else:
        print(f"[run_s2] Using cached dataset: {DATA_CSV}")
        data_source = "cached"
        csv_path    = DATA_CSV

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")

    # Apply column mapping for Kaggle variants
    df = df.rename(columns={k: v for k, v in COLUMN_MAPPING.items() if k in df.columns})

    # Ensure pipeline-expected columns exist (add NaN proxy if missing)
    for col in ["cpu_usage", "memory_usage", "disk_io", "uptime_seconds",
                "network_latency_ms", "throughput_mbps"]:
        if col not in df.columns:
            df[col] = float("nan")

    # perspective column required by pipelines
    if "perspective" not in df.columns:
        node_to_persp = {
            "node-local-01":  "LOCAL",
            "node-hub-01":    "CENTRAL",
            "node-oracle-01": "EXTERNAL",
        }
        df["perspective"] = df["node_id"].map(node_to_persp).fillna("LOCAL")

    print(f"[run_s2] Dataset loaded: {len(df):,} rows  source={data_source}")
    return df, data_source


def _run_pipelines(df: pd.DataFrame) -> dict[str, list[dict]]:
    all_signals = {}
    runners = {
        "otel":      pipeline_otel.run,
        "datamesh":  pipeline_datamesh.run,
        "dsig":      pipeline_dsig.run,
        "otel_dsig": pipeline_otel_dsig.run,
    }
    for name, fn in runners.items():
        print(f"[run_s2] Running pipeline: {name} ...", end=" ", flush=True)
        t0      = time.perf_counter()
        sigs    = fn(df)
        elapsed = time.perf_counter() - t0
        print(f"{len(sigs)} signals in {elapsed:.1f}s")
        all_signals[name] = sigs
    return all_signals


def _write_raw_outputs(all_signals: dict, data_source: str):
    for name, sigs in all_signals.items():
        out_path = os.path.join(RAW_DIR, f"{name}.json")
        payload  = {"pipeline": name, "data_source": data_source, "signals": sigs}
        with open(out_path, "w") as f:
            json.dump(payload, f, indent=2, default=str)
        print(f"[run_s2] Raw output → {out_path}  ({len(sigs)} signals)")


def _compute_metrics(all_signals: dict, gt: dict,
                     llm_results: list[dict] | None) -> list[dict]:
    all_metrics = []
    for name in PIPELINE_NAMES:
        sigs = all_signals.get(name, [])
        m    = metrics_mod.compute_all(name, sigs, gt, llm_results)
        all_metrics.append(m)
        print(f"[run_s2] Metrics [{name}]: "
              f"M02={m['M02_signal_compactness_bytes']}B  "
              f"M03={m['M03_noise_reduction_ratio_pct']}%  "
              f"M09_FAR={m['M09_false_alarm_rate_pct']}%")
    return all_metrics


def _write_summary_csv(all_metrics: list[dict]):
    out_path = os.path.join(RESULTS_DIR, "summary.csv")
    if not all_metrics:
        return

    flat_rows = []
    for row in all_metrics:
        flat = {}
        for k, v in row.items():
            if isinstance(v, dict):
                for sub_k, sub_v in v.items():
                    flat[f"{k}.{sub_k}"] = sub_v
            else:
                flat[k] = v
        flat_rows.append(flat)

    flat_fieldnames = list(flat_rows[0].keys()) if flat_rows else []
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=flat_fieldnames)
        writer.writeheader()
        writer.writerows(flat_rows)

    print(f"[run_s2] Summary CSV → {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    force_synthetic = "--synthetic" in sys.argv
    skip_llm        = "--skip-llm"  in sys.argv

    print("=" * 60)
    print("D-SIG Stress Test — Scenario 2: Network Throughput Stress")
    print("=" * 60)

    _ensure_dirs()

    # Step 1 — Ground truth
    gt = _load_ground_truth()
    print(f"[run_s2] Ground truth loaded: {len(gt['incidents'])} incidents")

    # Step 2 — Dataset
    df, data_source = _load_data(force_synthetic)

    # Step 3 — Pipelines
    all_signals = _run_pipelines(df)
    _write_raw_outputs(all_signals, data_source)

    # Step 4 — LLM evaluation
    llm_results = None
    if not skip_llm:
        print("[run_s2] Starting LLM evaluation (16 calls) ...")
        try:
            llm_results = llm_eval.run_all_evaluations(all_signals, gt)
            llm_path = os.path.join(RESULTS_DIR, "llm_responses.json")
            with open(llm_path, "w") as f:
                json.dump(llm_results, f, indent=2, default=str)
            print(f"[run_s2] LLM responses → {llm_path}")
        except EnvironmentError as e:
            print(f"[run_s2] WARNING: {e}  — skipping LLM evaluation.")
        except Exception as e:
            print(f"[run_s2] ERROR during LLM evaluation: {e}  — continuing without LLM metrics.")
    else:
        print("[run_s2] LLM evaluation skipped (--skip-llm).")

    # Step 5 — Metrics
    all_metrics  = _compute_metrics(all_signals, gt, llm_results)
    metrics_path = os.path.join(RESULTS_DIR, "metrics_report.json")
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)
    print(f"[run_s2] Metrics report → {metrics_path}")

    # Step 6 — Summary CSV
    _write_summary_csv(all_metrics)

    print("=" * 60)
    print("Scenario 2 complete. Results in results/scenario2/")
    print("=" * 60)


if __name__ == "__main__":
    main()
