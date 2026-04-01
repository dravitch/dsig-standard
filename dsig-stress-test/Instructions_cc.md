# Instructions Claude Code — D-SIG Stress Test · LLM Evaluation Run

## Prerequisite: .env file

Create `dsig-stress-test/.env` with your Anthropic API key:

    ANTHROPIC_API_KEY=sk-ant-...

This file is already in `.gitignore` and will never be committed.

## Run scenario2_corrected with full LLM evaluation

    cd dsig-stress-test
    set -a && source .env && set +a
    DSIG_RESULTS_DIR=results/scenario2_corrected \
      python scenario2/run_scenario2.py --synthetic

Expected output:
- 16 LLM calls (4 incidents × 4 pipelines)
- `results/scenario2_corrected/llm_responses.json` created
- `results/scenario2_corrected/metrics_report.json` updated with:
  - M01_decision_latency_s  — non-null for all 4 pipelines
  - M07_interpretability_score — non-null for all 4 pipelines
  - M08_trust_accumulation_utility — 100.0 for otel_dsig, 0.0 for dsig (valid)

## Commit the updated results

    git add results/scenario2_corrected/
    git commit -m "feat: scenario2_corrected — M01/M07 populated via LLM evaluation"
    git push -u origin claude/review-dsig-stress-test-81Pcn
