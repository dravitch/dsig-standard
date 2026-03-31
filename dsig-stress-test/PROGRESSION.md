# D-SIG Stress Test — Progression

**Date** : 2026-03-30
**Branche** : `claude/review-dsig-stress-test-81Pcn`
**Statut** : Scenario 1 exécuté ✅

---

## Scenario 1 — IT Node Vitality Monitoring

### Exécution
- Dataset : synthétique v1 (4 320 lignes, 3 nodes × 1 440 min, 4 incidents injectés)
- Pipelines : 4 exécutés sur les mêmes données brutes
- LLM : 16 appels (4 pipelines × 4 incidents) — `claude-sonnet-4-6`, prompt fixe

### Résultats bruts (M01–M10)

| Pipeline   | M02 Compactness | M03 Noise Reduction | M07 Interpretability | M09 False Alarm |
|------------|-----------------|---------------------|----------------------|-----------------|
| OTel       | 279.9 B         | 67.7 %              | 9.0 / 10             | 0.0 %           |
| Data Mesh  | 553.4 B         | 36.2 %              | 9.0 / 10             | 0.0 %           |
| D-SIG      | 704.1 B         | 18.8 %              | 5.8 / 10             | 0.0 %           |
| OTel→D-SIG | 702.3 B         | 19.0 %              | 7.2 / 10             | 0.0 %           |

### Fichiers générés
- `results/scenario1/metrics_report.json` — 10 métriques × 4 pipelines
- `results/scenario1/llm_responses.json` — 16 réponses LLM avec `input_tokens_to_llm`
- `results/scenario1/summary.csv` — tableau plat pour DeepSeek
- `results/scenario1/raw_outputs/*.json` — signaux bruts des 4 pipelines
- `results/scenario1/ANALYSIS_PROTOCOL.md` — 2 asymétries documentées

### Notes techniques
- Fix appliqué : `process_count` en float (accepte NaN pour silences)
- Loader `.env` : affectation directe (`os.environ[k] = v`) — surcharge nix-shell
- `.gitignore` ajouté : `.env`, `.venv/`, datasets CSV, raw_outputs

### Prochaine étape
Transmission des fichiers à DeepSeek pour analyse objective (sans complaisance).

---

## À faire (Scenarios 2 & 3)
- Scenario 2 : throughput réseau
- Scenario 3 : OTel demo live
- Lancer uniquement si Scenario 1 validé sans ajustement majeur
