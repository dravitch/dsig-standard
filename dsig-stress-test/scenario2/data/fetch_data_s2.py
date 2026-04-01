"""
fetch_data_s2.py — Dataset acquisition for Scenario 2.

Strategy:
1. Try Kaggle API download (brjapon/servers-throughput-vs-latency).
2. If Kaggle unavailable, generate a synthetic dataset with the same schema and
   the 4 incidents injected at the timestamps defined in ground_truth_s2.json.

Output: data/network_metrics.csv
Columns: timestamp, network_latency_ms, cpu_usage, memory_usage,
         uptime_seconds, disk_io, throughput_mbps, node_id, perspective
"""

import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd

DATA_DIR   = os.path.dirname(__file__)
OUTPUT_CSV = os.path.join(DATA_DIR, "network_metrics.csv")
GT_PATH    = os.path.join(os.path.dirname(DATA_DIR), "ground_truth_s2.json")

# Simulation parameters
SIM_START     = pd.Timestamp("2026-04-01T00:00:00Z")
FREQ_MINUTES  = 1           # 1 point per minute
TOTAL_MINUTES = 24 * 60     # 1440 per node

NODES = {
    "node-local-01":  "LOCAL",
    "node-hub-01":    "CENTRAL",
    "node-oracle-01": "EXTERNAL",
}

# Kaggle column mapping → pipeline schema
KAGGLE_COLUMN_MAP = {
    "latency":        "network_latency_ms",
    "response_time":  "network_latency_ms",
    "cpu":            "cpu_usage",
    "cpu_usage":      "cpu_usage",
    "memory":         "memory_usage",
    "mem":            "memory_usage",
    "memory_usage":   "memory_usage",
    "uptime":         "uptime_seconds",
    "io":             "disk_io",
    "disk_io":        "disk_io",
    "throughput":     "throughput_mbps",
    "bandwidth":      "throughput_mbps",
    "server_id":      "node_id",
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
             "brjapon/servers-throughput-vs-latency",
             "--unzip", "-p", DATA_DIR],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            for fname in os.listdir(DATA_DIR):
                if fname.endswith(".csv") and fname != "network_metrics.csv":
                    return os.path.join(DATA_DIR, fname)
    except Exception:
        pass
    return None


def normalize_kaggle_df(df):
    """Rename Kaggle columns to pipeline schema; add node_id and perspective."""
    df = df.rename(columns={k: v for k, v in KAGGLE_COLUMN_MAP.items() if k in df.columns})

    # Ensure all required columns exist
    required = ["timestamp", "network_latency_ms", "cpu_usage", "memory_usage",
                "uptime_seconds", "disk_io", "throughput_mbps"]
    for col in required:
        if col not in df.columns:
            df[col] = np.nan

    if "node_id" not in df.columns:
        df["node_id"] = "node-local-01"
    if "perspective" not in df.columns:
        df["perspective"] = "LOCAL"

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    return df[["timestamp", "network_latency_ms", "cpu_usage", "memory_usage",
               "uptime_seconds", "disk_io", "throughput_mbps", "node_id", "perspective"]]


# ---------------------------------------------------------------------------
# Synthetic generation
# ---------------------------------------------------------------------------

def _baseline_series(n, low, high, seed):
    rng = np.random.default_rng(seed)
    vals = np.clip(
        rng.normal(loc=(low + high) / 2, scale=(high - low) / 6, size=n),
        low, high
    )
    return vals


def generate_synthetic(gt):
    """Generate 4320+ rows covering all nodes and all 4 S2 incidents."""
    timestamps = pd.date_range(SIM_START, periods=TOTAL_MINUTES, freq="min", tz="UTC")
    frames = []

    for node_id, perspective in NODES.items():
        n         = TOTAL_MINUTES
        seed_base = hash(node_id) % (2**31)

        lat        = _baseline_series(n, 5,  15,  seed_base + 1)
        cpu        = _baseline_series(n, 30, 55,  seed_base + 2)
        mem        = _baseline_series(n, 40, 65,  seed_base + 3)
        uptime     = np.arange(1, n + 1, dtype=float) * 60   # seconds since boot
        disk       = _baseline_series(n, 10, 50,  seed_base + 4)
        throughput = _baseline_series(n, 80, 120, seed_base + 5)  # Mbps nominal

        for inc in gt["incidents"]:
            t_start = int(inc["t_start_h"] * 60)
            t_end   = int(inc["t_end_h"]   * 60)
            itype   = inc["type"]
            cause   = inc["cause"]

            if itype == "throughput_burst" and cause == perspective:
                # LOCAL only: latency spikes to 250ms, throughput × 3, CPU spikes
                duration = max(1, t_end - t_start)
                for i, t in enumerate(range(t_start, min(t_end, n))):
                    frac = i / duration
                    # Latency ramp: 10ms → 250ms → back down
                    peak_frac = 1 - abs(2 * frac - 1)   # 0 → 1 → 0
                    lat[t]        = 10 + peak_frac * 240
                    throughput[t] = throughput[t] * (1 + 2 * peak_frac)  # × up to 3
                    cpu[t]        = min(95, cpu[t] + peak_frac * 40)

            elif itype == "isp_degradation" and cause == perspective:
                # EXTERNAL: latency 8ms → 400ms progressive
                duration = max(1, t_end - t_start)
                for i, t in enumerate(range(t_start, min(t_end, n))):
                    frac  = i / duration
                    lat[t] = 8 + frac * 392   # 8 → 400

            elif itype == "silence_oracle" and inc.get("silent_source") == perspective:
                # EXTERNAL goes silent
                for t in range(t_start, min(t_end, n)):
                    lat[t]        = np.nan
                    cpu[t]        = np.nan
                    mem[t]        = np.nan
                    uptime[t]     = np.nan
                    disk[t]       = np.nan
                    throughput[t] = np.nan

            elif itype == "baseline_cycles_break" and cause == perspective:
                # All perspectives: throughput drops to 10% of nominal
                for t in range(t_start, min(t_end, n)):
                    throughput[t] = throughput[t] * 0.10
                    lat[t]        = lat[t] * 3
                    cpu[t]        = min(95, cpu[t] + 25)

        df = pd.DataFrame({
            "timestamp":          timestamps,
            "network_latency_ms": lat,
            "cpu_usage":          cpu,
            "memory_usage":       mem,
            "uptime_seconds":     uptime,
            "disk_io":            disk,
            "throughput_mbps":    throughput,
            "node_id":            node_id,
            "perspective":        perspective,
        })
        frames.append(df)

    full = pd.concat(frames, ignore_index=True)
    full = full.sort_values(["timestamp", "node_id"]).reset_index(drop=True)
    return full


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def fetch(force_synthetic=False):
    gt          = _load_ground_truth()
    data_source = "unknown"

    if not force_synthetic:
        kaggle_csv = try_kaggle_download()
        if kaggle_csv:
            print(f"[fetch_data_s2] Kaggle download succeeded: {kaggle_csv}")
            df          = pd.read_csv(kaggle_csv)
            df          = normalize_kaggle_df(df)
            data_source = "kaggle"
        else:
            print("[fetch_data_s2] Kaggle unavailable — generating synthetic_s2 dataset.")
            df          = generate_synthetic(gt)
            data_source = "synthetic_s2"
    else:
        print("[fetch_data_s2] Force synthetic mode.")
        df          = generate_synthetic(gt)
        data_source = "synthetic_s2"

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[fetch_data_s2] Saved {len(df):,} rows → {OUTPUT_CSV}  (source={data_source})")
    return OUTPUT_CSV, data_source


if __name__ == "__main__":
    force = "--synthetic" in sys.argv
    fetch(force_synthetic=force)
