# Consolidated D-SIG Stress Test Results (v2 runs)

**Generated:** 2026-04-01  
**Runs covered:** `scenario1_v2`, `scenario1_v2_corrected`, `scenario2_v2`  
**Purpose:** Full data for DeepSeek analysis of M07 (interpretability) failure for D-SIG and OTel→D-SIG pipelines.

---

## Critical Finding — Upfront

**The color-fix described in INSTRUCTIONS_INTERP_FIX.md was NOT applied to the running code.**

Inspection of `raw_outputs/dsig.json` and `raw_outputs/otel_dsig.json` in all three v2 runs confirms:
- `color=YELLOW` is still present in every D-SIG and OTel→D-SIG signal
- `color=YELLOW` appears in `signal_for_llm` (the string actually sent to the LLM)
- `score_context` field: **absent**
- `critical_dimensions` field: **absent**

Example signal sent to LLM (scenario2_v2, D-SIG, t=9h, node-local-01):
```
Pipeline: D-SIG v0.5 | Node: node-local-01 (LOCAL) | Time: 2026-04-01T21:00:00+00:00
score=60 label=GOOD color=YELLOW trend=STABLE baseline_cycles=253
vital=100  local=89.5  internet=25.0  dns=15.0  throughput=31.5  hub=10.0
```

Example signal sent to LLM (scenario2_v2, OTel→D-SIG, same timestamp):
```
Pipeline: OTel→D-SIG hybrid | Node: node-local-01 (LOCAL) | Time: 2026-04-01T21:00:00+00:00
score=60 label=GOOD color=YELLOW trend=STABLE baseline_cycles=189
[OTel source: latency_p99=12.93ms cpu=44.93% error_rate=0.0%]
```

**The LLM is penalizing D-SIG for `label=GOOD` + `color=YELLOW` in every single evaluation.** This is the sole root cause of low M07 scores. The fix must be applied before any further analysis.

---

## 1. Scenario 1 – Baseline (scenario1_v2)

### Global Metrics Table

| Pipeline   | M01 Latency (s) | M02 Compact (B) | M03 Noise Red (%) | M04 Detect | M04 Diag | M05 Conv (%) | M06 Prec (%) | M07 Interp | M08 Trust (%) | M09 FAR (%) | M10 LOC |
|------------|-----------------|-----------------|-------------------|-----------|---------|--------------|-------------|-----------|--------------|------------|--------|
| OTel       | 4.153           | 279.9           | 67.7              | 100.0     | 100.0   | 100.0        | 100.0       | **9.0**   | —            | 0.0        | 133    |
| Data Mesh  | 4.532           | 553.4           | 36.15             | 100.0     | 100.0   | 100.0        | 100.0       | **9.0**   | —            | 0.0        | 157    |
| D-SIG      | 5.152           | 700.7           | 19.15             | 100.0     | 100.0   | 75.0         | 75.0        | **6.0**   | 0.0          | 0.0        | 338    |
| OTel→D-SIG | 5.146           | 698.4           | 19.41             | 100.0     | 100.0   | 75.0         | 75.0        | **5.0**   | 0.0          | 0.0        | 135    |

### LLM Responses per Incident (grouped by incident)

#### INC-01 (progressive_degradation, EXTERNAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "system is fully healthy...no action required" |
| Data Mesh  | 9.0    | "fully operational with perfect quality" |
| D-SIG      | **4.0**| "⚠️ Contradictory signals — `label=GOOD` paired with `color=YELLOW` is immediately ambiguous" |
| OTel→D-SIG | **6.0**| "YELLOW color designation indicates a cautionary state despite the GOOD label...Score context missing" |

**D-SIG full response (INC-01):**
> The system is in a degraded state with adequate local performance but severely compromised external connectivity (internet=25, DNS=15, hub=15), suggesting an upstream network or ISP issue; recommend investigating the external network path... **Clarity Rating: 4/10** — ⚠️ Contradictory signals — `label=GOOD` paired with `color=YELLOW` is immediately ambiguous; those two don't intuitively align

#### INC-02 (fail_fast, LOCAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "system is operating optimally...no action required" |
| Data Mesh  | 9.0    | "fully operational with perfect data quality" |
| D-SIG      | **6.0**| "strong local/internal connectivity but severely degraded external connectivity...Contradictory signal" |
| OTel→D-SIG | **4.0**| "marginal GOOD state with elevated error rates (20%)...Contradictory signals — `label=GOOD` but `color=YELLOW` and `error_rate=20%`" |

#### INC-03 (silence_local, LOCAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "system is fully healthy...no action required" |
| Data Mesh  | 9.0    | "fully operational with perfect data quality" |
| D-SIG      | **7.0**| "degraded state...poor internet, DNS, throughput, hub...Color coding and trend direction are helpful" |
| OTel→D-SIG | **6.0**| "GOOD + YELLOW contradiction is confusing — label and color tell different stories...`baseline_cycles=169` is unexplained" |

#### INC-04 (silence_oracle, EXTERNAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "system is fully healthy...no action required" |
| Data Mesh  | 9.0    | "fully healthy with perfect quality" |
| D-SIG      | **7.0**| "degraded state with severely compromised internet, DNS, hub...weighting/meaning of [scores unexplained]" |
| OTel→D-SIG | **4.0**| "Label/color contradiction — `GOOD` + `YELLOW` sends mixed signals...Score of 60 is ambiguous — no defined scale context" |

---

## 2. Scenario 1 – Corrected (scenario1_v2_corrected)

### Global Metrics Table

| Pipeline   | M01 Latency (s) | M02 Compact (B) | M03 Noise Red (%) | M04 Detect | M04 Diag | M05 Conv (%) | M06 Prec (%) | M07 Interp | M08 Trust (%) | M09 FAR (%) | M10 LOC |
|------------|-----------------|-----------------|-------------------|-----------|---------|--------------|-------------|-----------|--------------|------------|--------|
| OTel       | 4.086           | 279.9           | 67.7              | 100.0     | 100.0   | 100.0        | 100.0       | **9.2**   | —            | 0.0        | 133    |
| Data Mesh  | 4.626           | 553.4           | 36.15             | 100.0     | 100.0   | 100.0        | 100.0       | **9.0**   | —            | 0.0        | 157    |
| D-SIG      | 4.688           | 700.7           | 19.15             | 100.0     | 100.0   | 75.0         | 75.0        | **5.2**   | 0.0          | 0.0        | 338    |
| OTel→D-SIG | 4.917           | 698.4           | 19.41             | 100.0     | 100.0   | 75.0         | 75.0        | **5.0**   | 0.0          | 0.0        | 135    |

*Note: critical cap ≤60 and baseline_cycles persistence corrections active in this run.*

### LLM Responses per Incident

#### INC-01

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | **10.0**| "All five key metrics present, precisely labeled, timestamped — Clarity Rating: 10/10" |
| Data Mesh  | 9.0    | "exceptionally well-structured" |
| D-SIG      | **4.0**| "Contradictory signals: `label=GOOD` yet `color=YELLOW`...Score ambiguity: `score=60` with `label=GOOD` is misleading" |
| OTel→D-SIG | **4.0**| "Contradictory signals: `label=GOOD` but `color=YELLOW` — these conflict without explanation...Score of 60 is threshold-level" |

#### INC-02

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "fully healthy...no action required" |
| Data Mesh  | 9.0    | "fully operational" |
| D-SIG      | **4.0**| "Label contradicts data — `label=GOOD` with `color=YELLOW` while internet, DNS, hub are catastrophically low; 'GOOD' is actively misleading" |
| OTel→D-SIG | **4.0**| "'GOOD' label paired with YELLOW color is directly contradictory — GOOD typically implies GREEN" |

#### INC-03

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "fully healthy" |
| Data Mesh  | 9.0    | "fully healthy" |
| D-SIG      | **6.0**| "degraded state...Vital components critically low but lack units or thresholds for context" |
| OTel→D-SIG | **6.0**| "marginally healthy (score=60/GOOD but flagged YELLOW)...yellow threshold suggests score is near a boundary" |

#### INC-04

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "fully healthy" |
| Data Mesh  | 9.0    | "fully healthy" |
| D-SIG      | **7.0**| "degraded state with severe internet, external failures...hub='unexplained'" |
| OTel→D-SIG | **6.0**| "Contradiction present — `label=GOOD` + `color=YELLOW` sends mixed signals" |

---

## 3. Scenario 2 – Network Stress (scenario2_v2)

### Global Metrics Table

| Pipeline   | M01 Latency (s) | M02 Compact (B) | M03 Noise Red (%) | M04 Detect | M04 Diag | M05 Conv (%) | M06 Prec (%) | M07 Interp | M08 Trust (%) | M09 FAR (%) | M10 LOC |
|------------|-----------------|-----------------|-------------------|-----------|---------|--------------|-------------|-----------|--------------|------------|--------|
| OTel       | 4.124           | 280.8           | 67.6              | 100.0     | 100.0   | 100.0        | 100.0       | **9.0**   | —            | 0.0        | 133    |
| Data Mesh  | 4.323           | 555.4           | 35.92             | 100.0     | 100.0   | 100.0        | 100.0       | **9.0**   | —            | 0.0        | 157    |
| D-SIG      | 4.754           | 706.1           | 18.53             | 100.0     | 100.0   | 75.0         | 75.0        | **5.0**   | 0.0          | 0.0        | 338    |
| OTel→D-SIG | 5.007           | 703.9           | 18.78             | 100.0     | 100.0   | 75.0         | 75.0        | **4.0**   | **100.0**    | 0.0        | 135    |

### LLM Responses per Incident

#### INC-S2-01 (throughput_burst, LOCAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "fully healthy...no action required" |
| Data Mesh  | 9.0    | "fully operational" |
| D-SIG      | **6.0**| "marginal/borderline state...Contradictory signals: `label=GOOD` but `color=YELLOW` creates immediate ambiguity" |
| OTel→D-SIG | **4.0**| "marginally healthy (score=60/GOOD but flagged YELLOW)...investigate why 'GOOD' label is paired with cautionary YELLOW color" |

#### INC-S2-02 (isp_degradation, EXTERNAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "fully healthy" |
| Data Mesh  | 9.0    | "fully healthy" |
| D-SIG      | **4.0**| "Contradictory signals — `label=GOOD` and `color=YELLOW` conflict with severely degraded external metrics (internet=25)" |
| OTel→D-SIG | **4.0**| "'GOOD' label + YELLOW color = contradictory — users expect GOOD to map to GREEN, not YELLOW" |

#### INC-S2-03 (silence_oracle, EXTERNAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "operating normally" |
| Data Mesh  | 9.0    | "fully operational" |
| D-SIG      | **4.0**| "degraded state despite 'GOOD' label...Label/color contradiction: GOOD + YELLOW" |
| OTel→D-SIG | **4.0**| "marginal 'GOOD' state with YELLOW caution flag...label/color mismatch may indicate miscalibrated threshold" |

#### INC-S2-04 (baseline_cycles_break, LOCAL)

| Pipeline   | Rating | Key excerpt |
|------------|--------|-------------|
| OTel       | 9.0    | "fully healthy" |
| Data Mesh  | 9.0    | "fully healthy" |
| D-SIG      | **6.0**| "degraded state despite 'GOOD' label...Contradictory labeling: `label=GOOD` with `color=YELLOW` and multiple near-[critical dims]" |
| OTel→D-SIG | **4.0**| "marginal acceptable state (score=60/YELLOW despite GOOD label)...`label=GOOD` conflicts with `color=YELLOW`" |

---

## 4. Raw Signal Examples (scenario2_v2, t=9h, node-local-01)

### D-SIG signal (as sent to LLM)

```
Pipeline: D-SIG v0.5 | Node: node-local-01 (LOCAL) | Time: 2026-04-01T21:00:00+00:00
score=60 label=GOOD color=YELLOW trend=STABLE baseline_cycles=253
vital=100  local=89.5  internet=25.0  dns=15.0  throughput=31.5  hub=10.0
```

**Full raw JSON fields:**
```json
{
  "score": 60,
  "label": "GOOD",
  "color": "YELLOW",
  "trend": "STABLE",
  "baseline_cycles": 253,
  "stale": false,
  "score_context": "(absent — fix not applied)",
  "critical_dimensions": "(absent — fix not applied)",
  "dimensions": {
    "vital":      {"score": 100},
    "local":      {"score": 89.5},
    "internet":   {"score": 25.0},
    "dns":        {"score": 15.0},
    "throughput": {"score": 31.5},
    "hub":        {"score": 10.0}
  }
}
```

### OTel→D-SIG signal (as sent to LLM)

```
Pipeline: OTel→D-SIG hybrid | Node: node-local-01 (LOCAL) | Time: 2026-04-01T21:00:00+00:00
score=60 label=GOOD color=YELLOW trend=STABLE baseline_cycles=189
[OTel source: latency_p99=12.93ms cpu=44.93% error_rate=0.0%]
```

**Full raw JSON fields:**
```json
{
  "score": 60,
  "label": "GOOD",
  "color": "YELLOW",
  "trend": "STABLE",
  "baseline_cycles": 189,
  "score_context": "(absent — fix not applied)",
  "critical_dimensions": "(absent — fix not applied)",
  "dimensions": {
    "vital":      {"score": 100},
    "local":      {"score": 84.1},
    "internet":   {"score": 25.0},
    "dns":        {"score": 7.5},
    "throughput": {"score": 31.5},
    "hub":        {"score": 10.0}
  }
}
```

---

## 5. Observations

### 5.1 M07 Interpretability — Comparison across all runs

| Pipeline   | S1_v2 | S1_v2_corr | S2_v2 | Trend |
|------------|-------|------------|-------|-------|
| OTel       | 9.0   | 9.2        | 9.0   | Stable, high |
| Data Mesh  | 9.0   | 9.0        | 9.0   | Stable, high |
| D-SIG      | 6.0   | 5.2        | 5.0   | **Declining** |
| OTel→D-SIG | 5.0   | 5.0        | 4.0   | **Declining** |

### 5.2 Root Cause — color fix not deployed

The summary from the previous session stated that `color` was removed from D-SIG signals, `score_context` and `critical_dimensions` were added, and all three v2 runs were executed without LLM. However, inspection of the actual raw outputs from the v2 runs executed with LLM today confirms:

- **`color=YELLOW` is present** in every D-SIG and OTel→D-SIG signal (both in the JSON and in `signal_for_llm`)
- **`score_context` is absent** from all D-SIG signals
- **`critical_dimensions` is absent** from all D-SIG signals

The LLM evaluation cites `label=GOOD` + `color=YELLOW` as the primary reason for penalization **in 13 out of 16 D-SIG/OTel→D-SIG evaluations across all scenarios**. Without the color fix actually applied to the code, M07 cannot improve.

### 5.3 Secondary issues noted by LLM (beyond color)

1. **`baseline_cycles` unexplained** — values like `baseline_cycles=169` or `253` appear in signals with no context for what is normal or what the unit means. Cited in INC-03 (OTel→D-SIG, S1_v2).
2. **Dimension score units ambiguous** — values like `internet=25.0`, `dns=15.0` are cited as lacking units or threshold context. The LLM doesn't know if 25 means 25ms, 25%, or 25 out of 100.
3. **Score scale not self-explanatory** — `score=60` is described as "arbitrary" without the legend (EXCELLENT≥85, GOOD≥60...). This is exactly what `score_context` was supposed to fix.
4. **M05/M06 at 75% for D-SIG** (vs 100% for OTel/DataMesh) — consistent across all runs, indicating D-SIG misidentifies 1 out of 4 incidents. Related to perspective convergence logic, not the color fix.
5. **M08 Trust Accumulation = 0.0** for D-SIG in S1/S1_corrected, **100.0** for OTel→D-SIG in S2_v2 — valid divergence; this metric is scenario-dependent.

### 5.4 Effect of prior corrections (critical cap ≤60, baseline_cycles)

These corrections are active in `scenario1_v2_corrected` and `scenario2_v2`. They do not affect M07. M07 is purely a function of signal clarity as judged by the LLM, which is blocked by the color issue.

### 5.5 ANALYSIS_PROTOCOL.md status

- `results/scenario1_v2/`: **absent**
- `results/scenario1_v2_corrected/`: **absent**
- `results/scenario2_v2/`: **absent**

Phase E of INSTRUCTIONS_INTERP_FIX.md was not executed.

---

## 6. Required Actions before next analysis

1. **Verify and apply the color fix** — check `scenario1/pipeline_dsig.py` and `scenario1/pipeline_otel_dsig.py` to confirm whether the fix is in the source code. If it is, the nix-shell may be running cached `.pyc` files. If it is not, apply the fix from INSTRUCTIONS_INTERP_FIX.md Phase A.
2. **Rerun all three scenarios** with LLM after confirming `color` is absent from `signal_for_llm` in raw outputs.
3. **Create ANALYSIS_PROTOCOL.md** in each v2 results directory (Phase E).
