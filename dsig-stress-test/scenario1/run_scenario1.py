"""
run_scenario1.py — Orchestrator for D-SIG Stress Test · Scenario 1.

Usage:
    python scenario1/run_scenario1.py [--synthetic] [--skip-llm]

    --synthetic   Force synthetic dataset generation (skip Kaggle attempt)
    --skip-llm    Skip LLM evaluation (useful for dry runs without API key)

Single command, no interactive input.

Steps:
    1. Load ground truth
    2. Fetch / generate dataset
    3. Run all 4 pipelines on the same raw data
    4. For each pipeline × each incident: extract signal, call LLM
    5. Compute all 10 metrics per pipeline
    6. Write results/scenario1/
       - raw_outputs/*.json
       - metrics_report.json
       - llm_responses.json
       - summary.csv
       - ANALYSIS_PROTOCOL.md (if not already present)
"""

import csv
import json
import os
import sys
import time

# Charger .env si présent (jamais versionné — voir .env.example)
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ[_k.strip()] = _v.strip().strip('"').strip("'")

import pandas as pd

# Ensure scenario1/ is on the path so local imports work
sys.path.insert(0, os.path.dirname(__file__))

import pipeline_otel
import pipeline_datamesh
import pipeline_dsig
import pipeline_otel_dsig
import metrics as metrics_mod
import llm_eval

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCENARIO_DIR  = os.path.dirname(__file__)
ROOT_DIR      = os.path.dirname(SCENARIO_DIR)
RESULTS_DIR   = os.environ.get("DSIG_RESULTS_DIR",
                    os.path.join(ROOT_DIR, "results", "scenario1"))
RAW_DIR       = os.path.join(RESULTS_DIR, "raw_outputs")
GT_PATH       = os.path.join(SCENARIO_DIR, "ground_truth.json")
DATA_CSV      = os.path.join(SCENARIO_DIR, "data", "it_metrics.csv")

PIPELINE_NAMES = ["otel", "datamesh", "dsig", "otel_dsig"]


def _ensure_dirs():
    for d in [RESULTS_DIR, RAW_DIR]:
        os.makedirs(d, exist_ok=True)


def _load_ground_truth() -> dict:
    with open(GT_PATH) as f:
        return json.load(f)


def _load_data(force_synthetic: bool) -> tuple[pd.DataFrame, str]:
    """Return (dataframe, data_source_str). Fetch if CSV not present."""
    # Import here to avoid circular issues; data dir is a sub-package
    sys.path.insert(0, os.path.join(SCENARIO_DIR, "data"))
    import fetch_data
    if not os.path.exists(DATA_CSV):
        csv_path, data_source = fetch_data.fetch(force_synthetic=force_synthetic)
    else:
        print(f"[run] Using cached dataset: {DATA_CSV}")
        data_source = "cached"
        csv_path    = DATA_CSV

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    # Ensure timezone awareness
    if df["timestamp"].dt.tz is None:
        df["timestamp"] = df["timestamp"].dt.tz_localize("UTC")
    print(f"[run] Dataset loaded: {len(df):,} rows  source={data_source}")
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
        print(f"[run] Running pipeline: {name} ...", end=" ", flush=True)
        t0 = time.perf_counter()
        sigs = fn(df)
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
        print(f"[run] Raw output → {out_path}  ({len(sigs)} signals)")


def _compute_metrics(all_signals: dict, gt: dict,
                     llm_results: list[dict] | None) -> list[dict]:
    all_metrics = []
    for name in PIPELINE_NAMES:
        sigs = all_signals.get(name, [])
        m    = metrics_mod.compute_all(name, sigs, gt, llm_results)
        all_metrics.append(m)
        print(f"[run] Metrics [{name}]: "
              f"M02={m['M02_signal_compactness_bytes']}B  "
              f"M03={m['M03_noise_reduction_ratio_pct']}%  "
              f"M09_FAR={m['M09_false_alarm_rate_pct']}%")
    return all_metrics


def _write_summary_csv(all_metrics: list[dict]):
    out_path = os.path.join(RESULTS_DIR, "summary.csv")
    if not all_metrics:
        return

    fieldnames = list(all_metrics[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_metrics:
            # Flatten nested dicts for CSV
            flat = {}
            for k, v in row.items():
                if isinstance(v, dict):
                    for sub_k, sub_v in v.items():
                        flat[f"{k}.{sub_k}"] = sub_v
                else:
                    flat[k] = v
            # Write with flattened fieldnames
            writer.writerow({fn: flat.get(fn, row.get(fn)) for fn in fieldnames})

    # Write a clean version with flattened keys
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

    print(f"[run] Summary CSV → {out_path}")


def _write_analysis_protocol():
    """Create ANALYSIS_PROTOCOL.md in results/scenario1/ if not already present."""
    proto_path = os.path.join(RESULTS_DIR, "ANALYSIS_PROTOCOL.md")
    if os.path.exists(proto_path):
        return
    src = os.path.join(ROOT_DIR, "results", "scenario1", "ANALYSIS_PROTOCOL.md")
    # Will be created by the initial file creation step; skip silently if missing
    print(f"[run] ANALYSIS_PROTOCOL.md expected at {proto_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    force_synthetic = "--synthetic"   in sys.argv
    skip_llm        = "--skip-llm"    in sys.argv

    # --output-dir <path> overrides DSIG_RESULTS_DIR and the default
    if "--output-dir" in sys.argv:
        idx = sys.argv.index("--output-dir")
        if idx + 1 < len(sys.argv):
            global RESULTS_DIR, RAW_DIR
            RESULTS_DIR = sys.argv[idx + 1]
            RAW_DIR     = os.path.join(RESULTS_DIR, "raw_outputs")

    print("=" * 60)
    print("D-SIG Stress Test — Scenario 1: IT Node Vitality Monitoring")
    print("=" * 60)

    _ensure_dirs()

    # Step 1 — Ground truth
    gt = _load_ground_truth()
    print(f"[run] Ground truth loaded: {len(gt['incidents'])} incidents")

    # Step 2 — Dataset
    df, data_source = _load_data(force_synthetic)

    # Step 3 — Pipelines
    all_signals = _run_pipelines(df)
    _write_raw_outputs(all_signals, data_source)

    # Step 4 — LLM evaluation
    llm_results = None
    if not skip_llm:
        print("[run] Starting LLM evaluation (16 calls) ...")
        try:
            llm_results = llm_eval.run_all_evaluations(all_signals, gt)
            llm_path = os.path.join(RESULTS_DIR, "llm_responses.json")
            with open(llm_path, "w") as f:
                json.dump(llm_results, f, indent=2, default=str)
            print(f"[run] LLM responses → {llm_path}")
        except EnvironmentError as e:
            print(f"[run] WARNING: {e}  — skipping LLM evaluation.")
        except Exception as e:
            print(f"[run] ERROR during LLM evaluation: {e}  — continuing without LLM metrics.")
    else:
        print("[run] LLM evaluation skipped (--skip-llm).")

    # Step 5 — Metrics
    all_metrics = _compute_metrics(all_signals, gt, llm_results)
    metrics_path = os.path.join(RESULTS_DIR, "metrics_report.json")
    with open(metrics_path, "w") as f:
        json.dump(all_metrics, f, indent=2, default=str)
    print(f"[run] Metrics report → {metrics_path}")

    # Step 6 — Summary CSV
    _write_summary_csv(all_metrics)
    _write_analysis_protocol()

    print("=" * 60)
    print("Scenario 1 complete. Results in results/scenario1/")
    print("=" * 60)


if __name__ == "__main__":
    main()
