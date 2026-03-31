# ANALYSIS_PROTOCOL.md — D-SIG Stress Test · Scenario 1

**Version**: 1.0  
**Date**: 2026-03-30  
**Status**: Pre-defined before execution (immutable reference)

This document describes the two explicit asymmetries in the evaluation methodology,
as required by the README validation consensus (Grok / Claude / DeepSeek).

---

## Asymmetry 1 — `input_tokens_to_llm` logged separately per pipeline

**Rationale**: The four pipelines produce signals of fundamentally different sizes
and information density. OTel produces verbose OpenMetrics text; D-SIG produces a
compact structured signal; Data Mesh produces a JSON data product. When the LLM
evaluates each signal, the number of tokens it receives is not identical.

**Implication**: Decision latency (M01) is influenced by both:
1. The LLM inference time (fair comparison).
2. The tokenisation cost of the signal itself (pipeline-dependent).

**Protocol**: `llm_responses.json` logs `input_tokens_to_llm` for every call.
DeepSeek MUST report M01 both as raw latency (seconds) and normalised by
`input_tokens_to_llm` to separate "signal quality" from "signal verbosity".

**Field in output**: `input_tokens_to_llm` in `llm_responses.json`.

---

## Asymmetry 2 — Silence Resilience (M04) decomposed into two sub-components

**Rationale**: "Silence resilience" conflates two distinct capabilities:

1. **Detection** — Did the pipeline notice that a source went silent?
   - OTel: stale flag after 2 missed cycles.
   - Data Mesh: `stale: true` + `stale_duration_minutes`.
   - D-SIG: TTL exceeded → STALE signal with `trend: CRITICAL_FALL` (Rule 8).

2. **Diagnosis** — Did the pipeline identify which perspective was silent AND
   correctly isolate the cause (e.g., "LOCAL silent but EXTERNAL nominal →
   not an ISP issue")?
   - OTel and Data Mesh have no native divergence model; diagnosis requires
     external correlation.
   - D-SIG's multi-perspective architecture and Prusik principle make this
     a structural capability, not an add-on.

**Protocol**: M04 is reported as `{detection_score: 0-100, diagnostic_score: 0-100}`.
A pipeline that detects silence but cannot diagnose cause scores high on detection
and low (or null) on diagnostic. DeepSeek MUST NOT aggregate these two sub-scores
into a single number.

**Fields in output**: `M04_silence_resilience.detection_score` and
`M04_silence_resilience.diagnostic_score` in `metrics_report.json`.

---

## Ground Truth Reference

All incident evaluations are made against `scenario1/ground_truth.json`
(committed before any pipeline execution, SHA-verifiable).

| Incident | Type                | Cause    | Silent Source |
|----------|---------------------|----------|---------------|
| INC-01   | progressive_degradation | EXTERNAL | —         |
| INC-02   | fail_fast           | LOCAL    | —             |
| INC-03   | silence_local       | LOCAL    | LOCAL         |
| INC-04   | silence_oracle      | EXTERNAL | EXTERNAL      |

---

## False Alarm Definition (M09)

| Pipeline   | Alert condition                                           |
|------------|-----------------------------------------------------------|
| OTel       | latency_p99 ≥ 30ms OR error_rate ≥ 1% OR stale=true      |
| Data Mesh  | status ∈ {DEGRADED, CRITICAL, STALE}                     |
| D-SIG      | label ∈ {DEGRADED, CRITICAL} OR stale=true               |
| OTel→D-SIG | Same as D-SIG (final signal is D-SIG)                    |

A false alarm is any alert raised outside ±10 minutes of a real incident window.

---

## Result Files

| File                       | Consumer  | Notes                              |
|----------------------------|-----------|------------------------------------|
| `raw_outputs/*.json`       | Audit     | Full signal list per pipeline      |
| `metrics_report.json`      | DeepSeek  | 10 metrics per pipeline            |
| `llm_responses.json`       | DeepSeek  | Raw LLM responses + token counts   |
| `summary.csv`              | DeepSeek  | Flat table — rows=pipelines, cols=metrics |

DeepSeek receives `metrics_report.json` and `summary.csv`.
DeepSeek does NOT receive `raw_outputs/` (too large; available for audit only).

---

*This protocol is immutable once execution begins.*  
*Any deviation must be documented as an amendment with a reason.*
