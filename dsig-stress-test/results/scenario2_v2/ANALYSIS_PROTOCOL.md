# ANALYSIS_PROTOCOL.md — D-SIG Stress Test · Scenario 2 v2

**Version**: 2.0
**Date**: 2026-04-02
**Status**: Pre-defined before execution (immutable reference)
**Supersedes**: `results/scenario2/ANALYSIS_PROTOCOL.md` (v1.0) and
`results/scenario2_corrected/ANALYSIS_PROTOCOL.md` (v1.1)

---

## Interpretability Fix — Applied before v2 runs

**Problem identified:** `color=YELLOW` combined with `label=GOOD` caused
systematic M07 penalty. In universal monitoring convention, YELLOW=WARNING,
not GOOD. The LLM (and any human unfamiliar with D-SIG) interpreted this
as a signal inconsistency.

**Fix applied:**
1. `color` field removed from emitted D-SIG signals (dashboard-only hint,
   not a decision signal component) — comment: `# COLOR REMOVED — interpretability fix`
2. `score_context` added to every signal (fixed legend string)
3. `critical_dimensions` added when cap is active (list of capped dimension names)
4. M07 LLM prompt updated with label/trend independence note

**Standard note:** D-SIG v0.5 §3.3 defines YELLOW=GOOD. This color mapping
conflicts with universal monitoring convention. Documented as a known friction
point for v0.6 consideration. The fix removes color from the test signal to
eliminate the collision without modifying the standard.

**Non-regression:** OTel and Data Mesh pipelines unchanged. Color field was
never part of their output format.

---

## Dataset & Column Mapping

Identical to v1.0. See `results/scenario2/ANALYSIS_PROTOCOL.md`.

| Pipeline column expected | S2 source column | Proxy / Notes |
|--------------------------|------------------|---------------|
| `network_latency_ms`     | `latency` / `response_time` | Direct mapping |
| `cpu_usage`              | `cpu` / `cpu_usage` | Direct mapping |
| `memory_usage`           | `memory` / `mem` | NaN proxy if absent |
| `uptime_seconds`         | `uptime` | Simulated as `minute_index × 60` if absent |
| `disk_io`                | `io` / `disk_io` | Default NaN if absent |
| `throughput_mbps`        | `throughput` / `bandwidth` | Logged in raw outputs |
| `node_id`                | `server_id` / `node_id` | COLUMN_MAPPING applied |
| `perspective`            | derived from `node_id` | LOCAL/CENTRAL/EXTERNAL |

---

## Asymmetry 1 — `input_tokens_to_llm` logged separately per pipeline

`llm_responses.json` logs `input_tokens_to_llm` for every call.
DeepSeek MUST report M01 both as raw latency (seconds) and normalised by
`input_tokens_to_llm` to separate "signal quality" from "signal verbosity".

With the interpretability fix, D-SIG signals are larger (added `score_context`
and `critical_dimensions`). DeepSeek MUST compare `input_tokens_to_llm` for
dsig_v2 vs dsig_v1 to quantify the compactness cost of self-explanation.

---

## Asymmetry 2 — Silence Resilience (M04) decomposed

INC-S2-03 (`silence_oracle`): same protocol as v1.

- `detection_score`: did the pipeline notice EXTERNAL went silent?
- `diagnostic_score`: was EXTERNAL correctly isolated as the cause?

---

## INC-S2-04 — baseline_cycles Trust Accumulation

baseline_cycles correctly accumulates starting at cycle 1 (bug fixed in
previous session). At t=17h (pre-break), all nodes have bc ≥ 200.

DeepSeek MUST log:
- `baseline_cycles` at the last window before INC-S2-04 (t≈18:55)
- `baseline_cycles` at the first window during INC-S2-04 (t=19:00)
- Whether otel_dsig detects the reset (expected: yes via p99 latency sensitivity)
- Whether dsig detects the reset (expected: no — 5-min averages mask the spike)

This divergence between dsig and otel_dsig for M08 is a valid finding:
OTel p99 is more sensitive to burst events than 5-min window averages.

---

## Phase A Correction Inheritance — Critical Cap Active + self-documented

The cap `score ≤ 60 if any(internet|dns|hub) < 30` is implemented in
`scenario1/pipeline_dsig.py`. When active, the signal now includes:
```json
"critical_dimensions": ["internet", "dns", "hub"]
```
This removes the opaque "why is the score capped?" question for any consumer.

---

## False Alarm Definition (M09)

Same as Scenario 1 and Scenario 2 v1.

---

## Ground Truth Reference

`scenario2/ground_truth_s2.json` (immutable since creation).

| Incident   | Type                   | Cause    | Silent Source |
|------------|------------------------|----------|---------------|
| INC-S2-01  | throughput_burst       | LOCAL    | —             |
| INC-S2-02  | isp_degradation        | EXTERNAL | —             |
| INC-S2-03  | silence_oracle         | EXTERNAL | EXTERNAL      |
| INC-S2-04  | baseline_cycles_break  | LOCAL    | —             |

---

## Version Comparison for DeepSeek

| Result set | Cap | bc fix | color removed | score_context | LLM prompt |
|------------|-----|--------|---------------|---------------|------------|
| scenario2  | no  | no     | no            | no            | v1         |
| scenario2_corrected | yes | yes | no       | no            | v1         |
| scenario2_v2 | yes | yes   | yes           | yes           | v2         |

DeepSeek should compare M07 across these three sets to quantify the
interpretability fix impact independently from the baseline_cycles fix impact.

---

*This protocol is immutable once execution begins.*
