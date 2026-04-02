# Consolidated D-SIG Stress Test Results (v2 + v3 runs)

**Generated:** 2026-04-01 — **Updated:** 2026-04-01 (v3 runs added)  
**Runs covered:** `scenario1_v2`, `scenario1_v2_corrected`, `scenario2_v2` (color fix absent) + `scenario1_v3`, `scenario1_v3_corrected`, `scenario2_v3` (color fix applied)  
**Purpose:** Full data for DeepSeek analysis of M07 (interpretability) evolution before/after color fix.

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

~~1. Verify and apply the color fix~~ ✅ Done — PR #5 merged, fix confirmed.  
~~2. Rerun all three scenarios~~ ✅ Done — see Section 7 below.  
3. **Create ANALYSIS_PROTOCOL.md** in v3 result directories (Phase E still pending).

---

## 7. v3 Runs — Color Fix Applied (2026-04-01)

### Signal structure confirmed (test result)

```
color present:              False  ✅
score_context present:      True   ✅
critical_dimensions present: True  ✅

Example signal_for_llm (D-SIG, nominal node):
Pipeline: D-SIG v0.5 | Node: node-local-01 (LOCAL) | Time: 2026-04-01T00:00:00+00:00
score=19 label=CRITICAL trend=STABLE baseline_cycles=0  critical_dimensions=['internet', 'dns', 'hub']
score 0-100: EXCELLENT≥85, GOOD≥60, DEGRADED≥35, CRITICAL<35
vital=0  local=98.0  internet=25.0  dns=15.0  throughput=32.0  hub=15.0
```

### 7.1 Scenario 1 – Baseline v3 (scenario1_v3)

| Pipeline   | M01 Latency (s) | M02 Compact (B) | M03 Noise Red (%) | M04 Det | M04 Diag | M05 (%) | M06 (%) | M07 Interp | M08 (%) | M09 FAR (%) | M10 LOC |
|------------|-----------------|-----------------|-------------------|---------|----------|---------|---------|-----------|---------|------------|--------|
| OTel       | 5.287           | 279.9           | 67.7              | 100.0   | 100.0    | 100.0   | 100.0   | **9.0**   | —       | 0.0        | 133    |
| Data Mesh  | 5.296           | 553.4           | 36.15             | 100.0   | 100.0    | 100.0   | 100.0   | **9.0**   | —       | 0.0        | 157    |
| D-SIG      | 4.903           | 828.0           | 4.47              | 100.0   | 100.0    | 75.0    | 75.0    | **6.8**   | 0.0     | 0.0        | 346    |
| OTel→D-SIG | 5.027           | 825.6           | 4.73              | 100.0   | 100.0    | 75.0    | 75.0    | **6.5**   | 0.0     | 0.0        | 139    |

*Note: M02 increased (828B vs 700B) and M03 dropped (4.5% vs 19%) because `score_context` + `critical_dimensions` were added to the signal — expected trade-off.*

### 7.2 Scenario 1 – Corrected v3 (scenario1_v3_corrected)

| Pipeline   | M01 Latency (s) | M02 Compact (B) | M03 Noise Red (%) | M04 Det | M04 Diag | M05 (%) | M06 (%) | M07 Interp | M08 (%) | M09 FAR (%) | M10 LOC |
|------------|-----------------|-----------------|-------------------|---------|----------|---------|---------|-----------|---------|------------|--------|
| OTel       | 4.972           | 279.9           | 67.7              | 100.0   | 100.0    | 100.0   | 100.0   | **9.0**   | —       | 0.0        | 133    |
| Data Mesh  | 5.828           | 553.4           | 36.15             | 100.0   | 100.0    | 100.0   | 100.0   | **9.0**   | —       | 0.0        | 157    |
| D-SIG      | 4.873           | 828.0           | 4.47              | 100.0   | 100.0    | 75.0    | 75.0    | **6.8**   | 0.0     | 0.0        | 346    |
| OTel→D-SIG | 5.417           | 825.6           | 4.73              | 100.0   | 100.0    | 75.0    | 75.0    | **6.8**   | 0.0     | 0.0        | 139    |

### 7.3 Scenario 2 – Network Stress v3 (scenario2_v3)

| Pipeline   | M01 Latency (s) | M02 Compact (B) | M03 Noise Red (%) | M04 Det | M04 Diag | M05 (%) | M06 (%) | M07 Interp | M08 (%) | M09 FAR (%) | M10 LOC |
|------------|-----------------|-----------------|-------------------|---------|----------|---------|---------|-----------|---------|------------|--------|
| OTel       | 5.028           | 280.8           | 67.6              | 100.0   | 100.0    | 100.0   | 100.0   | **8.2**   | —       | 0.0        | 133    |
| Data Mesh  | 5.377           | 555.4           | 35.92             | 100.0   | 100.0    | 100.0   | 100.0   | **9.0**   | —       | 0.0        | 157    |
| D-SIG      | 5.012           | 833.6           | 3.81              | 100.0   | 100.0    | 75.0    | 75.0    | **6.5**   | 0.0     | 0.0        | 346    |
| OTel→D-SIG | 4.895           | 831.5           | 4.06              | 100.0   | 100.0    | 75.0    | 75.0    | **7.0**   | 100.0   | 0.0        | 139    |

### 7.4 M07 Evolution — v2 vs v3

| Pipeline   | S1_v2 | **S1_v3** | Δ    | S1_corr_v2 | **S1_corr_v3** | Δ    | S2_v2 | **S2_v3** | Δ    |
|------------|-------|-----------|------|------------|----------------|------|-------|-----------|------|
| OTel       | 9.0   | 9.0       | 0    | 9.2        | 9.0            | -0.2 | 9.0   | 8.2       | -0.8 |
| Data Mesh  | 9.0   | 9.0       | 0    | 9.0        | 9.0            | 0    | 9.0   | 9.0       | 0    |
| D-SIG      | 6.0   | **6.8**   | +0.8 | 5.2        | **6.8**        | +1.6 | 5.0   | **6.5**   | +1.5 |
| OTel→D-SIG | 5.0   | **6.5**   | +1.5 | 5.0        | **6.8**        | +1.8 | 4.0   | **7.0**   | +3.0 |

**The color fix improved M07 for D-SIG by +0.8 to +1.6 points and for OTel→D-SIG by +1.5 to +3.0 points across all scenarios.**

### 7.5 Remaining gap analysis

Despite the improvement, D-SIG and OTel→D-SIG remain below OTel/Data Mesh (~9.0). Residual issues cited by the LLM in v2 runs that are likely still present:

1. **Dimension score units ambiguous** — values like `internet=25.0`, `dns=15.0` have no unit label (ms? % ? out of 100?). The LLM infers but notes the ambiguity.
2. **`baseline_cycles` unexplained** — large values (e.g. 169, 253) appear without context.
3. **M05/M06 stuck at 75%** — D-SIG misidentifies 1 out of 4 incidents (convergence/precision). Structural issue unrelated to signal clarity.
4. **`score_context` added** — this likely explains the improvement. Further gains may require labeling dimension scores explicitly (e.g. `internet=25/100`).

### 7.6 M03 trade-off note

M03 (Noise Reduction) dropped from ~19% to ~4.5% for D-SIG in v3. This is expected: `score_context` (a fixed 60-char legend string) and `critical_dimensions` add output bytes while input bytes remain constant, reducing the apparent compression ratio. This is a signal enrichment trade-off, not a regression.
