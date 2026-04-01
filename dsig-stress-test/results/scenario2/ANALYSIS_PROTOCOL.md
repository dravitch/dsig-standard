# ANALYSIS_PROTOCOL.md — D-SIG Stress Test · Scenario 2

**Version**: 1.0
**Date**: 2026-04-01
**Status**: Pre-defined before execution (immutable reference)

---

## Dataset & Column Mapping

**Target dataset**: Kaggle `brjapon/servers-throughput-vs-latency`
**Fallback**: Synthetic `synthetic_s2` (4320 rows, 3 nodes × 1440 min)

| Pipeline column expected | S2 source column | Proxy / Notes |
|--------------------------|------------------|---------------|
| `network_latency_ms`     | `latency` / `response_time` | Direct mapping |
| `cpu_usage`              | `cpu` / `cpu_usage` | Direct mapping |
| `memory_usage`           | `memory` / `mem` | Direct if available; else NaN (half-credit = 50%) |
| `uptime_seconds`         | `uptime` | Simulated as `minute_index × 60` if absent |
| `disk_io`                | `io` / `disk_io` | Default NaN if absent → DNS half-credit (7.5 pts) |
| `throughput_mbps`        | `throughput` / `bandwidth` | S2-specific column; not used by existing scoring functions but logged in raw outputs |
| `node_id`                | `server_id` / `node_id` | COLUMN_MAPPING applied in run_scenario2.py |
| `perspective`            | derived from `node_id` | `node-local-01=LOCAL`, `node-hub-01=CENTRAL`, `node-oracle-01=EXTERNAL` |

`throughput_mbps` is present in the dataset to enable INC-S2-01 (throughput_burst)
detection but is not consumed by existing pipeline scoring functions. It is
logged in raw outputs for future D-SIG extensions.

---

## Asymmetry 1 — `input_tokens_to_llm` logged separately per pipeline

Identical protocol to Scenario 1 (ANALYSIS_PROTOCOL.md v1.0).

`llm_responses.json` logs `input_tokens_to_llm` for every call.
DeepSeek MUST report M01 both as raw latency (seconds) and normalised by
`input_tokens_to_llm` to separate "signal quality" from "signal verbosity".

---

## Asymmetry 2 — Silence Resilience (M04) decomposed into two sub-components

**Incident INC-S2-03** (`silence_oracle`) tests this asymmetry:

- **Detection** — Did the pipeline notice that EXTERNAL went silent?
  - OTel: stale flag after 2 missed cycles.
  - Data Mesh: `stale: true` + `stale_duration_minutes`.
  - D-SIG: TTL exceeded → STALE + `trend: CRITICAL_FALL` (Rule 8).

- **Diagnosis** — Did the pipeline correctly isolate EXTERNAL as the silent
  source, while reporting LOCAL and CENTRAL as nominal?
  - D-SIG structural advantage: multi-perspective divergence model (Rule 9)
    makes this a native capability, not an add-on.

**Protocol**: M04 is reported as `{detection_score: 0-100, diagnostic_score: 0-100}`.
A pipeline that detects silence but cannot diagnose the cause scores high on
detection and low (or null) on diagnostic. DeepSeek MUST NOT aggregate these
two sub-scores into a single number.

---

## INC-S2-04 — baseline_cycles Trust Accumulation Utility

**Incident INC-S2-04** (`baseline_cycles_break` at t=19h) tests M08:

- At t=18h (before break): `baseline_cycles` should be high (≈ 180+ increments
  after 18h of multi-perspective convergence within 30 pts).
- At t=19h (during break): all 3 perspectives diverge simultaneously.
  `baseline_cycles` resets to 0.

DeepSeek MUST log:
- `baseline_cycles` value at the last window before INC-S2-04
- `baseline_cycles` value at the first window during INC-S2-04
- Whether D-SIG and OTel→D-SIG correctly flagged the rupture vs baseline

---

## Phase A Correction Inheritance — Critical Cap Active

The cap `score ≤ 60 if any(internet|dns|hub) < 30` is implemented in
`scenario1/pipeline_dsig.py` (commit `fix: critical dimension cap ≤60`).

`run_scenario2.py` imports `pipeline_dsig` from `scenario1/` via
`sys.path.insert`. The cap is therefore **automatically active** in all
Scenario 2 D-SIG and OTel→D-SIG signals. No additional modification required.

---

## False Alarm Definition (M09)

Same as Scenario 1:

| Pipeline   | Alert condition                                           |
|------------|-----------------------------------------------------------|
| OTel       | latency_p99 ≥ 30ms OR error_rate ≥ 1% OR stale=true      |
| Data Mesh  | status ∈ {DEGRADED, CRITICAL, STALE}                     |
| D-SIG      | label ∈ {DEGRADED, CRITICAL} OR stale=true               |
| OTel→D-SIG | Same as D-SIG (final signal is D-SIG)                    |

A false alarm is any alert raised outside ±10 minutes of a real incident window.

---

## Ground Truth Reference

All incident evaluations are made against `scenario2/ground_truth_s2.json`
(committed before any pipeline execution, SHA-verifiable).

| Incident   | Type                   | Cause    | Silent Source |
|------------|------------------------|----------|---------------|
| INC-S2-01  | throughput_burst       | LOCAL    | —             |
| INC-S2-02  | isp_degradation        | EXTERNAL | —             |
| INC-S2-03  | silence_oracle         | EXTERNAL | EXTERNAL      |
| INC-S2-04  | baseline_cycles_break  | LOCAL    | —             |

---

## Result Files

| File                       | Consumer  | Notes                              |
|----------------------------|-----------|------------------------------------|
| `raw_outputs/*.json`       | Audit     | Full signal list per pipeline      |
| `metrics_report.json`      | DeepSeek  | 10 metrics per pipeline            |
| `llm_responses.json`       | DeepSeek  | Raw LLM responses + token counts   |
| `summary.csv`              | DeepSeek  | Flat table — rows=pipelines, cols=metrics (same format as scenario1) |

DeepSeek receives `metrics_report.json` and `summary.csv`.
DeepSeek does NOT receive `raw_outputs/` (too large; available for audit only).

Cross-scenario comparison: `summary.csv` column schema is identical to
`results/scenario1_corrected/summary.csv` to allow direct side-by-side
analysis by DeepSeek.

---

*This protocol is immutable once execution begins.*
*Any deviation must be documented as an amendment with a reason.*
