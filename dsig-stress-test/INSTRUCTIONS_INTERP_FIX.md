# Instructions Claude Code — D-SIG Stress Test · Interpretability Fix

## Context

Post-analysis of Scenario 2 corrected results revealed a systematic
interpretability failure: the LLM evaluating M07 penalized D-SIG signals
for having `label=GOOD` combined with `color=YELLOW`. In universal monitoring
convention, YELLOW means WARNING or DEGRADED — not GOOD. D-SIG uses YELLOW for
the GOOD band (60–84), creating a semantic collision that produces artificially
low interpretability scores.

This is an implementation problem, not a standard design problem. The fix:
remove `color` from emitted signals in the test pipelines. The `label` field
carries the full semantic meaning. `color` is a dashboard visualization hint —
not a signal component for LLM or human decision-making in text form.

Additionally, two fields are added to make the signal self-sufficient for any
consumer unfamiliar with the D-SIG standard.

**Scope of changes:** `scenario1/pipeline_dsig.py`,
`scenario1/pipeline_otel_dsig.py`, `scenario1/llm_eval.py`, and the
`run_scenario*.py` orchestrators for output path control.

All corrections from previous sessions (critical cap ≤60, baseline_cycles
persistence) MUST remain intact. These are additive changes only.

---

## PHASE A — Signal structure fix (pipeline_dsig.py + pipeline_otel_dsig.py)

### A.1 Remove `color` from the emitted D-SIG signal

In `pipeline_dsig.py`, find the dictionary construction of the D-SIG signal
and remove the `color` key entirely from what is passed to `signal_for_llm`
and stored in `raw_outputs`.

The `color` field may remain in internal computation (for Grafana/dashboard
use) but MUST NOT appear in the `signal_for_llm` string sent to the LLM,
nor in the JSON stored in `raw_outputs/`.

```python
# BEFORE — causes semantic collision with universal monitoring convention
signal = {
    "dsig_version": "0.5",
    "score": score,
    "label": label,
    "color": color,      # REMOVE THIS from emitted signal
    "trend": trend,
    ...
}

# AFTER — label carries the semantic meaning, color is a visualization hint
signal = {
    "dsig_version": "0.5",
    "score": score,
    "label": label,      # GOOD / DEGRADED / CRITICAL / EXCELLENT
    "trend": trend,      # STABLE / IMPROVING / DEGRADING / CRITICAL_FALL
    "score_context": "score 0-100: EXCELLENT≥85, GOOD≥60, DEGRADED≥35, CRITICAL<35",
    ...
}
```

Add comment: `# COLOR REMOVED — interpretability fix: YELLOW≠GOOD in LLM/human convention`

### A.2 Add `score_context` field (fixed string)

Add to every emitted D-SIG signal:
```python
"score_context": "score 0-100: EXCELLENT≥85, GOOD≥60, DEGRADED≥35, CRITICAL<35"
```

This removes ambiguity about scale and thresholds for any consumer unfamiliar
with D-SIG.

### A.3 Add `critical_dimensions` field when cap is active

When the critical cap (≤60) is triggered, add to the signal:
```python
"critical_dimensions": [dim for dim, val in dim_scores.items()
                        if val < CRITICAL_THRESHOLD]
# Example output: ["internet", "dns"]
```

When the cap is NOT triggered, omit the field entirely (or set to empty list).

This explains to the LLM (and any human) exactly why the score was capped,
without requiring knowledge of the internal weighting logic.

### A.4 Apply identical changes to pipeline_otel_dsig.py

The OTel→D-SIG pipeline produces D-SIG signals at its output stage.
Apply the same three changes (remove color, add score_context, add
critical_dimensions) to the conversion function in `pipeline_otel_dsig.py`.

Verify that `baseline_cycles` is still propagated correctly from the D-SIG
pipeline (this was fixed in the previous session — confirm it survives this
edit).

---

## PHASE B — LLM evaluation prompt fix (llm_eval.py)

Update the fixed prompt used for M07 (Interpretability Score) to include
an explicit note on label/trend independence:

```python
PROMPT_FIXED = (
    "Given this signal, what is the system status and recommended action "
    "in one sentence? Rate the clarity of this signal on a scale of 1 to 10. "
    "Note: in this standard, 'label' indicates current state and 'trend' "
    "indicates momentum — they are independent. A label of GOOD with trend "
    "CRITICAL_FALL means the system is currently operational but deteriorating "
    "rapidly. This is intentional, not a contradiction."
)
```

Add comment: `# PROMPT UPDATED — label/trend independence clarification for M07`

---

## PHASE C — Full re-run from Scenario 1

The signal structure change affects all previously generated results.
All three scenarios must be re-run to produce consistent comparable data.

### C.1 Re-run Scenario 1 (baseline)

```bash
cd dsig-stress-test
python scenario1/run_scenario1.py --synthetic
```

Write results to: `results/scenario1_v2/`

Do NOT overwrite `results/scenario1/` (original baseline must be preserved
for historical comparison).

### C.2 Re-run Scenario 1 corrected (cap + baseline_cycles + interpretability fix)

```bash
python scenario1/run_scenario1.py --synthetic --output-dir results/scenario1_v2_corrected
```

If `--output-dir` parameter does not exist in `run_scenario1.py`, add it.

Write results to: `results/scenario1_v2_corrected/`

### C.3 Re-run Scenario 2 corrected (all fixes combined)

```bash
python scenario2/run_scenario2.py --synthetic
```

Write results to: `results/scenario2_v2/`

---

## PHASE D — Verification checklist

After all three runs, verify in the output JSON:

```
□ No `color` field in any D-SIG or OTel→D-SIG signal in raw_outputs/
□ `score_context` present in every D-SIG signal
□ `critical_dimensions` present when score was capped (non-empty list)
□ `critical_dimensions` absent or empty when score was not capped
□ `baseline_cycles` > 0 after the first 10 cycles (not stuck at 0)
□ `baseline_cycles` present and coherent in OTel→D-SIG signals
□ M07 score in summary.csv is present (not null) for all 4 pipelines
□ M01 (Decision Latency) present and non-zero
□ M08 (Trust Accumulation Utility) present and non-zero for INC-S2-04
□ OTel and Data Mesh results unchanged vs previous runs (non-regression)
```

---

## PHASE E — ANALYSIS_PROTOCOL update

Add a section to `results/scenario2_v2/ANALYSIS_PROTOCOL.md`:

```markdown
## Interpretability Fix — Applied before v2 runs

**Problem identified:** `color=YELLOW` combined with `label=GOOD` caused
systematic M07 penalty. In universal monitoring convention, YELLOW=WARNING,
not GOOD. The LLM (and any human unfamiliar with D-SIG) interpreted this
as a signal inconsistency.

**Fix applied:**
1. `color` field removed from emitted D-SIG signals (dashboard-only hint,
   not a decision signal component)
2. `score_context` added (fixed legend string)
3. `critical_dimensions` added when cap is active
4. M07 LLM prompt updated with label/trend independence note

**Standard note:** D-SIG v0.5 §3.3 defines YELLOW=GOOD. This color mapping
conflicts with universal monitoring convention. Documented as a known friction
point for v0.6 consideration. The fix removes color from the test signal to
eliminate the collision without modifying the standard.

**Non-regression:** OTel and Data Mesh pipelines unchanged. Color field was
never part of their output format.
```

---

## Commit structure

Three separate commits:

```
fix: remove color from D-SIG signal output — interpretability collision fix
fix: add score_context and critical_dimensions to D-SIG signal
fix: update M07 LLM prompt — label/trend independence clarification
```

Then one commit per result set:

```
results: scenario1_v2 — baseline with interpretability fix
results: scenario1_v2_corrected — all fixes combined
results: scenario2_v2 — full corrected run with interpretability fix
```

---

## Note for Grok

The test protocol (v0.3) does not need to be updated. The change is in the
signal emitted by the D-SIG pipelines — which is an implementation correction,
not a protocol change. The 10 metrics and their definitions remain identical.
Scenario 3 can proceed once DeepSeek validates scenario2_v2 results.
