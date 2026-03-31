Voici les instructions complètes pour Claude Code Web.

---

# Instructions Claude Code — D-SIG Stress Test · Scenario 2

## Contexte

Les pipelines du Scenario 1 sont dans `scenario1/` et restent la base de
référence. Le Scenario 2 les importe via `sys.path.insert`.

Ce fichier contient deux phases dans l'ordre strict d'exécution :
- **Phase A** : corriger les pipelines D-SIG du Scenario 1 (cap critique à 60)
- **Phase B** : construire et exécuter le Scenario 2

Ne pas commencer la Phase B avant que la Phase A soit terminée et validée.

---

## PHASE A — Correction des pipelines Scenario 1 (cap critique à 60)

### Contexte de la correction

Le Scenario 1 a révélé que le score D-SIG global peut être EXCELLENT ou GOOD
alors que des dimensions critiques (`internet`, `dns`, `hub`) sont en zone
CRITICAL (< 30). Cette contradiction nuit à l'interprétabilité.

### Fichiers à modifier

- `scenario1/pipeline_dsig.py`
- `scenario1/pipeline_otel_dsig.py`

### Modification technique

Dans la fonction qui calcule le score final (après la somme pondérée,
fail-fast, et précondition_gate), ajouter le plafonnement suivant :

```python
# Cap critique : si une dimension externe critique est < 30,
# le score global ne peut pas dépasser 60 (limite supérieure de GOOD).
# S'applique après fail-fast et précondition — ne les remplace pas.
CRITICAL_DIMS = ['internet', 'dns', 'hub']
CRITICAL_THRESHOLD = 30
CRITICAL_CAP = 60

dim_scores = {
    'internet': dims.get('internet', {}).get('score', 100),
    'dns':      dims.get('dns',      {}).get('score', 100),
    'hub':      dims.get('hub',      {}).get('score', 100),
}

if any(v < CRITICAL_THRESHOLD for v in dim_scores.values()):
    score = min(score_raw, CRITICAL_CAP)
else:
    score = score_raw
```

Règles D-SIG non modifiées :
- `label` et `color` restent dérivés du score final après plafonnement (Rule 10)
- `trend` calculé sur le score final
- Les valeurs individuelles dans `dimensions` restent inchangées

Ajouter un commentaire `# CRITICAL CAP v0.5 — DeepSeek correction` sur la
ligne du plafonnement dans les deux fichiers.

Ajouter une entrée dans `CHANGELOG.md` :
```
## [S1-corrected] - 2026-03-31
### Fixed
- pipeline_dsig.py : cap score à 60 si dimension critique (internet/dns/hub) < 30
- pipeline_otel_dsig.py : même correction appliquée au pipeline hybride
```

### Livrable Phase A

Relancer le Scenario 1 avec la correction :

```bash
python scenario1/run_scenario1.py --synthetic
```

Écrire les résultats dans `results/scenario1_corrected/` (pas dans
`results/scenario1/` — conserver les résultats originaux intacts).

Confirmer dans le terminal :
```
Phase A complete. Results in results/scenario1_corrected/
```

---

## PHASE B — Scenario 2 : Network Traffic & Throughput Stress Test

### Structure à créer

```
dsig-stress-test/
└── scenario2/
    ├── data/
    │   └── fetch_data_s2.py      ← dataset S2 + injection incidents
    ├── ground_truth_s2.json      ← vérité terrain pré-étiquetée (AVANT les pipelines)
    └── run_scenario2.py          ← orchestrateur S2
```

Les fichiers `pipeline_*.py`, `metrics.py`, `llm_eval.py` restent dans
`scenario1/` et sont importés depuis `run_scenario2.py`.

Résultats dans :
```
results/scenario2/
├── raw_outputs/
├── metrics_report.json
├── llm_responses.json
├── summary.csv
└── ANALYSIS_PROTOCOL.md
```

---

### Étape B-0 — Vérité terrain (ground_truth_s2.json)

Créer EN PREMIER. Immutable après création.

```json
{
  "scenario": "Network Traffic & Throughput Stress Test",
  "dataset": "Servers throughput vs latency (Kaggle)",
  "simulation_window": "24h",
  "focus": "Distillation sous charge réseau variable — burst, ISP dégradé, oracle silence, rupture baseline_cycles",
  "perspectives": {
    "LOCAL":    "Node réseau — throughput, latency, jitter, packet_loss",
    "CENTRAL":  "Hub — rolling 10min averages cross-nodes",
    "EXTERNAL": "Oracle — latency externe, disponibilité ISP"
  },
  "incidents": [
    {
      "id": "INC-S2-01",
      "t_start_h": 4,
      "t_end_h": 6,
      "type": "throughput_burst",
      "cause": "LOCAL",
      "description": "Pic de charge : throughput × 3, latency monte à 250ms, jitter élevé. LOCAL dégradé. CENTRAL et EXTERNAL nominaux.",
      "expected_diagnosis": "Surcharge locale. Pas de panne ISP.",
      "silent_source": null
    },
    {
      "id": "INC-S2-02",
      "t_start_h": 9,
      "t_end_h": 11,
      "type": "isp_degradation",
      "cause": "EXTERNAL",
      "description": "Dégradation ISP progressive : latency externe 8ms → 400ms sur 2h. LOCAL stable. CENTRAL voit la dégradation via hub. EXTERNAL dégrade en premier.",
      "expected_diagnosis": "ISP ou infrastructure externe. Systèmes locaux non affectés.",
      "silent_source": null
    },
    {
      "id": "INC-S2-03",
      "t_start_h": 15,
      "t_end_h": 16.5,
      "type": "silence_oracle",
      "cause": "EXTERNAL",
      "description": "Oracle (EXTERNAL) cesse d'émettre. LOCAL et CENTRAL nominaux. Test du principe PROD-02 : silence oracle = signal informatif.",
      "expected_diagnosis": "Problème du fournisseur de monitoring externe. Systèmes internes non affectés.",
      "silent_source": "EXTERNAL"
    },
    {
      "id": "INC-S2-04",
      "t_start_h": 19,
      "t_end_h": 20,
      "type": "baseline_cycles_break",
      "cause": "LOCAL",
      "description": "Rupture soudaine après 18h de convergence stable (baseline_cycles élevé). Throughput chute à 10% du nominal. Les 3 perspectives voient la dégradation simultanément.",
      "expected_diagnosis": "Rupture historique significative. Convergence multi-perspective confirme l'incident réel.",
      "silent_source": null
    }
  ]
}
```

---

### Étape B-1 — Dataset (fetch_data_s2.py)

**Dataset cible :**
Kaggle : `brjapon/servers-throughput-vs-latency`
Télécharger via `kaggle datasets download` si disponible.

**Schéma cible attendu par les pipelines :**

| Colonne attendue | Description | Source probable dans S2 |
|---|---|---|
| `timestamp` | ISO 8601 | à calculer ou mapper |
| `network_latency_ms` | latency réseau | `latency` ou `response_time` |
| `cpu_usage` | utilisation CPU % | `cpu` ou proxy via throughput |
| `memory_usage` | mémoire % | `memory` ou absent → proxy |
| `uptime_seconds` | uptime croissant | à simuler si absent |
| `disk_io` | I/O disque | absent probable → proxy 0.5 |
| `throughput_mbps` | débit réseau | `throughput` ou `bandwidth` |
| `node_id` | identifiant nœud | `server_id` ou à créer |

**Si le dataset S2 utilise des noms de colonnes différents**, ne pas modifier
les fichiers `pipeline_*.py`. Utiliser un dictionnaire `column_mapping` dans
`run_scenario2.py` pour renommer les colonnes avant de passer les données :

```python
COLUMN_MAPPING = {
    "latency":    "network_latency_ms",
    "cpu":        "cpu_usage",
    "mem":        "memory_usage",
    "uptime":     "uptime_seconds",
    "io":         "disk_io",
    "throughput": "throughput_mbps",
    "server_id":  "node_id",
}
df = df.rename(columns=COLUMN_MAPPING)
```

**Si une modification des pipelines est inévitable**, la limiter strictement
aux 5 fonctions de scoring dans `scenario1/pipeline_dsig.py`, commenter avec
`# SCENARIO2 ADAPTATION`, et vérifier que `run_scenario1.py` s'exécute
toujours sans erreur après la modification.

**Fallback synthétique** si Kaggle non disponible :
- Colonnes exactes : `timestamp`, `network_latency_ms`, `cpu_usage`,
  `memory_usage`, `uptime_seconds`, `disk_io`, `throughput_mbps`, `node_id`
- `throughput_mbps` est obligatoire pour INC-S2-01 (burst)
- Baseline : latency 5–15ms, throughput 80–120 Mbps, CPU 30–55%
- 3 nodes : `node-local-01` (LOCAL), `node-hub-01` (CENTRAL), `node-oracle-01` (EXTERNAL)
- 1 point/minute × 24h × 3 nodes = 4320 lignes minimum
- 4 incidents injectés aux timestamps de `ground_truth_s2.json`
- Logger `data_source = "kaggle"` ou `data_source = "synthetic_s2"`

---

### Étape B-2 — Orchestrateur (run_scenario2.py)

```python
import sys, os

# Import des pipelines depuis scenario1 — ne pas dupliquer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scenario1'))

from pipeline_otel      import run_otel_pipeline
from pipeline_datamesh  import run_datamesh_pipeline
from pipeline_dsig      import run_dsig_pipeline
from pipeline_otel_dsig import run_otel_dsig_pipeline
from metrics            import compute_all_metrics
from llm_eval           import evaluate_all_signals

SCENARIO_DIR = os.path.dirname(__file__)
RESULTS_DIR  = os.path.join(os.path.dirname(__file__), '..', 'results', 'scenario2')
GT_FILE      = os.path.join(SCENARIO_DIR, 'ground_truth_s2.json')  # S2 uniquement

# Même logique que run_scenario1.py
# 4 pipelines + métriques + LLM + export summary.csv
```

`summary.csv` doit avoir le même format que `results/scenario1/summary.csv`
pour permettre une comparaison directe entre scénarios par DeepSeek.

---

### Étape B-3 — ANALYSIS_PROTOCOL.md

Créer dans `results/scenario2/` avant l'exécution. Documenter :

1. **Mapping colonnes** : quelle colonne du dataset S2 correspond à quelle
   colonne attendue, et quels proxies ont été utilisés.

2. **Asymétrie Decision Latency** : `input_tokens_to_llm` loggué séparément
   pour chaque pipeline.

3. **Silence Resilience décomposée** : INC-S2-03 évaluée en deux
   sous-composantes indépendantes :
   - `detection_score` : le silence a-t-il été détecté ?
   - `diagnostic_score` : la cause est-elle correctement identifiée ?

4. **INC-S2-04 et baseline_cycles** : logger `baseline_cycles` à t=18h
   (avant rupture) et t=19h (après) pour quantifier Trust Accumulation Utility.

5. **Héritage correction Phase A** : confirmer que le cap critique à 60 est
   actif dans les pipelines D-SIG importés depuis scenario1/.

---

## Contraintes de livraison

- Phase A : `python scenario1/run_scenario1.py --synthetic` → `results/scenario1_corrected/`
- Phase B : `python scenario2/run_scenario2.py [--synthetic] [--skip-llm]`
- Aucun input interactif dans les deux phases
- Commit message Phase A : `fix: critical dimension cap ≤60 — pipeline_dsig + pipeline_otel_dsig`
- Commit message Phase B : `feat: scenario2 - network throughput stress test`
