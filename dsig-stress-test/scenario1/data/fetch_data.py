"""
fetch_data.py — Dataset acquisition for Scenario 1.

Strategy:
1. Try Kaggle API download (freshersstaff/it-system-performance-and-resource-metrics).
2. If Kaggle unavailable, generate a synthetic dataset with the same schema and
   the 4 incidents injected at the timestamps defined in ground_truth.json.

Output: data/it_metrics.csv
Columns: timestamp, cpu_usage, memory_usage, network_latency_ms,
         disk_io, process_count, uptime_seconds, node_id, perspective
"""

import json
import os
import subprocess
import sys
import time

import numpy as np
import pandas as pd

DATA_DIR = os.path.dirname(__file__)
OUTPUT_CSV = os.path.join(DATA_DIR, "it_metrics.csv")
GT_PATH = os.path.join(os.path.dirname(DATA_DIR), "ground_truth.json")

# Simulation parameters
SIM_START = pd.Timestamp("2026-03-30T00:00:00Z")
FREQ_MINUTES = 1           # 1 point per minute
TOTAL_MINUTES = 24 * 60    # 1440 per node

NODES = {
    "node-local-01":  "LOCAL",
    "node-hub-01":    "CENTRAL",
    "node-oracle-01": "EXTERNAL",
}


def _load_ground_truth():
    with open(GT_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Kaggle download
# ---------------------------------------------------------------------------

def try_kaggle_download():
    """Return path to downloaded CSV or None on failure."""
    try:
        result = subprocess.run(
            ["kaggle", "datasets", "download", "-d",
             "freshersstaff/it-system-performance-and-resource-metrics",
             "--unzip", "-p", DATA_DIR],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            # Find the first CSV in the directory
            for fname in os.listdir(DATA_DIR):
                if fname.endswith(".csv") and fname != "it_metrics.csv":
                    return os.path.join(DATA_DIR, fname)
    except Exception:
        pass
    return None


def normalize_kaggle_df(df):
    """Rename Kaggle columns to our schema; add node_id and perspective columns."""
    col_map = {
        # Common Kaggle column names for this dataset (best-effort)
        "Timestamp":        "timestamp",
        "CPU Usage (%)":    "cpu_usage",
        "Memory Usage (%)": "memory_usage",
        "Network Latency (ms)": "network_latency_ms",
        "Disk I/O (MB/s)":  "disk_io",
        "Process Count":    "process_count",
        "Uptime (seconds)": "uptime_seconds",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    required = ["timestamp", "cpu_usage", "memory_usage", "network_latency_ms",
                "disk_io", "process_count", "uptime_seconds"]
    for col in required:
        if col not in df.columns:
            df[col] = np.nan

    if "node_id" not in df.columns:
        df["node_id"] = "node-local-01"
    if "perspective" not in df.columns:
        df["perspective"] = "LOCAL"

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df[["timestamp", "cpu_usage", "memory_usage", "network_latency_ms",
               "disk_io", "process_count", "uptime_seconds", "node_id", "perspective"]]


# ---------------------------------------------------------------------------
# Synthetic generation
# ---------------------------------------------------------------------------

def _baseline_series(n, low, high, seed):
    rng = np.random.default_rng(seed)
    # Smooth random walk within [low, high]
    vals = np.clip(
        rng.normal(loc=(low + high) / 2, scale=(high - low) / 6, size=n),
        low, high
    )
    return vals


def generate_synthetic(gt):
    """Generate 4 320+ rows covering all nodes and all 4 incidents."""
    timestamps = pd.date_range(SIM_START, periods=TOTAL_MINUTES, freq="min", tz="UTC")
    frames = []

    for node_id, perspective in NODES.items():
        n = TOTAL_MINUTES
        seed_base = hash(node_id) % (2**31)

        cpu    = _baseline_series(n, 20, 60, seed_base + 1)
        mem    = _baseline_series(n, 40, 70, seed_base + 2)
        lat    = _baseline_series(n, 3,  8,  seed_base + 3)
        disk   = _baseline_series(n, 5,  50, seed_base + 4)
        procs  = _baseline_series(n, 80, 200, seed_base + 5).astype(int)
        uptime = np.arange(1, n + 1, dtype=float) * 60  # seconds since boot

        # -- Inject incidents per ground_truth --
        for inc in gt["incidents"]:
            t_start_min = int(inc["t_start_h"] * 60)
            t_end_min   = int(inc["t_end_h"]   * 60)
            itype       = inc["type"]
            cause       = inc["cause"]

            if itype == "progressive_degradation" and cause == perspective:
                # EXTERNAL node: latency 4ms → 180ms over the window
                duration = max(1, t_end_min - t_start_min)
                for i, t in enumerate(range(t_start_min, min(t_end_min, n))):
                    frac = i / duration
                    lat[t] = 4 + frac * 176  # 4 → 180

            elif itype == "fail_fast" and cause == perspective:
                # LOCAL node: uptime=0, CPU=0 at t_start
                t = t_start_min
                if t < n:
                    cpu[t]    = 0.0
                    uptime[t] = 0.0
                    procs[t]  = 0

            elif itype == "silence_local" and inc.get("silent_source") == perspective:
                # Mark as NaN — pipelines must detect absence
                for t in range(t_start_min, min(t_end_min, n)):
                    cpu[t]   = np.nan
                    mem[t]   = np.nan
                    lat[t]   = np.nan
                    disk[t]  = np.nan
                    procs[t] = np.nan
                    uptime[t] = np.nan

            elif itype == "silence_oracle" and inc.get("silent_source") == perspective:
                for t in range(t_start_min, min(t_end_min, n)):
                    cpu[t]   = np.nan
                    mem[t]   = np.nan
                    lat[t]   = np.nan
                    disk[t]  = np.nan
                    procs[t] = np.nan
                    uptime[t] = np.nan

        df = pd.DataFrame({
            "timestamp":           timestamps,
            "cpu_usage":           cpu,
            "memory_usage":        mem,
            "network_latency_ms":  lat,
            "disk_io":             disk,
            "process_count":       procs,
            "uptime_seconds":      uptime,
            "node_id":             node_id,
            "perspective":         perspective,
        })
        frames.append(df)

    full = pd.concat(frames, ignore_index=True)
    full = full.sort_values(["timestamp", "node_id"]).reset_index(drop=True)
    return full


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def fetch(force_synthetic=False):
    gt = _load_ground_truth()
    data_source = "unknown"

    if not force_synthetic:
        kaggle_csv = try_kaggle_download()
        if kaggle_csv:
            print(f"[fetch_data] Kaggle download succeeded: {kaggle_csv}")
            df = pd.read_csv(kaggle_csv)
            df = normalize_kaggle_df(df)
            data_source = "kaggle"
        else:
            print("[fetch_data] Kaggle unavailable — generating synthetic_v1 dataset.")
            df = generate_synthetic(gt)
            data_source = "synthetic_v1"
    else:
        print("[fetch_data] Force synthetic mode.")
        df = generate_synthetic(gt)
        data_source = "synthetic_v1"

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[fetch_data] Saved {len(df):,} rows → {OUTPUT_CSV}  (source={data_source})")
    return OUTPUT_CSV, data_source


if __name__ == "__main__":
    force = "--synthetic" in sys.argv
    fetch(force_synthetic=force)
