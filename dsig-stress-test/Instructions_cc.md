# Instructions Claude Code — D-SIG Stress Test · LLM Evaluation Run (v2)

## Prerequisite: .env file

Create `dsig-stress-test/.env` with your Anthropic API key:

    ANTHROPIC_API_KEY=sk-ant-...

This file is already in `.gitignore` and will never be committed.

## Source the API key

    cd dsig-stress-test
    set -a && source .env && set +a

## Run 1 — scenario1_v2 with full LLM evaluation

    python scenario1/run_scenario1.py --synthetic --output-dir results/scenario1_v2

Expected:
- 16 LLM calls (4 incidents × 4 pipelines)
- `results/scenario1_v2/llm_responses.json` created
- `results/scenario1_v2/metrics_report.json` updated with M01, M07 non-null

## Run 2 — scenario1_v2_corrected with full LLM evaluation

    python scenario1/run_scenario1.py --synthetic --output-dir results/scenario1_v2_corrected

## Run 3 — scenario2_v2 with full LLM evaluation

    DSIG_RESULTS_DIR=results/scenario2_v2 python scenario2/run_scenario2.py --synthetic

Expected for all three runs:
- M01_decision_latency_s — non-null for all 4 pipelines
- M07_interpretability_score — non-null, expected higher than prior runs (color removed)
- M08_trust_accumulation_utility — 100.0 for otel_dsig (INC-S2-04 or INC-S2-01)
- No `color` field in any D-SIG signal ✓
- `score_context` present in every D-SIG signal ✓
- `critical_dimensions` present when cap is active ✓

## Verification after each run

    python3 -c "
    import json
    for path in ['results/scenario1_v2/metrics_report.json',
                 'results/scenario1_v2_corrected/metrics_report.json',
                 'results/scenario2_v2/metrics_report.json']:
        print(path)
        with open(path) as f:
            for m in json.load(f):
                print(f'  {m[\"pipeline\"]:12} M01={m[\"M01_decision_latency_s\"]}  M07={m[\"M07_interpretability_score\"]}  M08={m[\"M08_trust_accumulation_utility\"]}')
        print()
    "

## Commit the updated results

    git add results/scenario1_v2/ results/scenario1_v2_corrected/ results/scenario2_v2/
    git commit -m "results: v2 runs with LLM evaluation — M01/M07 populated"
    git push -u origin claude/review-dsig-stress-test-81Pcn
