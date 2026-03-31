Voici les instructions complètes pour Claude Code Web.

---

# Instructions Claude Code — D-SIG Stress Test · Scenario 2

## Contexte

Les pipelines du Scenario 1 sont dans `scenario1/` et restent intacts.
Le Scenario 2 les importe via `sys.path.insert`. Tu crées uniquement ce qui est
nouveau. Tu ne touches à rien dans `scenario1/` sauf si une colonne du nouveau
dataset impose d'adapter les 5 fonctions de scoring dans `pipeline_dsig.py` —
et dans ce cas uniquement ces fonctions, documentées avec un commentaire
`# SCENARIO2 ADAPTATION`.

Les corrections du cahier des charges `INSTRUCTIONS.md` (cap critique à 60)
ont été appliquées au Scenario 1 ce soir. Elles sont déjà dans
`scenario1/pipeline_dsig.py` et `scenario1/pipeline_otel_dsig.py`.
Le Scenario 2 hérite de ces corrections automatiquement via l'import.

---

## Structure à créer

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

## Étape 0 — Vérité terrain (ground_truth_s2.json)

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

## Étape 1 — Dataset (fetch_data_s2.py)

### Dataset cible
Kaggle : `brjapon/servers-throughput-vs-latency`
Télécharger via `kaggle datasets download` si disponible.

### Mapping des colonnes vers le schéma D-SIG

Inspecter les colonnes disponibles et mapper vers le schéma attendu par les
pipelines. Logger le mapping dans `results/scenario2/ANALYSIS_PROTOCOL.md`.

**Schéma cible attendu par les pipelines (identique au Scenario 1) :**

| Colonne attendue | Description | Source probable dans S2 |
|---|---|---|
| `timestamp` | ISO 8601 | à calculer ou mapper |
| `network_latency_ms` | latency réseau | `latency` ou `response_time` |
| `cpu_usage` | utilisation CPU % | `cpu` ou proxy via throughput |
| `memory_usage` | mémoire % | `memory` ou absent → proxy |
| `uptime_seconds` | uptime croissant | à simuler si absent |
| `disk_io` | I/O disque | absent probable → proxy 0.5 |
| `node_id` | identifiant nœud | `server_id` ou à créer |

**Si une colonne est absente**, créer un proxy raisonnable et le documenter
dans `ANALYSIS_PROTOCOL.md`. Ne pas bloquer l'exécution.

### Fallback synthétique

Si l'API Kaggle n'est pas disponible, générer un dataset synthétique avec :
- Colonnes : identiques au Scenario 1
- Baseline : latency 5–15ms, throughput 80–120 Mbps, CPU 30–55%
- 3 nodes : `node-local-01` (LOCAL), `node-hub-01` (CENTRAL), `node-oracle-01` (EXTERNAL)
- Fréquence : 1 point/minute × 24h × 3 nodes = 4320 lignes minimum
- Les 4 incidents injectés aux timestamps de `ground_truth_s2.json`
- Logger `data_source = "kaggle"` ou `data_source = "synthetic_s2"`

**Différenciation obligatoire avec S1 :** les valeurs de throughput doivent être
explicitement présentes (même synthétiques) pour que INC-S2-01 (burst) soit
visible. Ajouter une colonne `throughput_mbps` si absente du dataset réel.

---

## Étape 2 — Orchestrateur (run_scenario2.py)

```python
import sys, os

# Import des pipelines depuis scenario1 — NE PAS DUPLIQUER
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scenario1'))

from pipeline_otel import run_otel_pipeline
from pipeline_datamesh import run_datamesh_pipeline
from pipeline_dsig import run_dsig_pipeline
from pipeline_otel_dsig import run_otel_dsig_pipeline
from metrics import compute_all_metrics
from llm_eval import evaluate_all_signals

SCENARIO_DIR = os.path.dirname(__file__)
RESULTS_DIR  = os.path.join(os.path.dirname(__file__), '..', 'results', 'scenario2')

# Charger ground_truth_s2.json (pas ground_truth.json du S1)
GT_FILE = os.path.join(SCENARIO_DIR, 'ground_truth_s2.json')

# Même logique que run_scenario1.py
# Les 4 pipelines + métriques + LLM + export summary.csv
```

**Point clé :** `ground_truth_s2.json` est chargé explicitement. Le code ne
doit jamais lire `ground_truth.json` du Scenario 1.

---

## Étape 3 — ANALYSIS_PROTOCOL.md

Créer dans `results/scenario2/` avant l'exécution. Documenter :

1. **Mapping colonnes** : quelle colonne du dataset S2 correspond à quelle
   colonne attendue, et quels proxies ont été utilisés.

2. **Asymétrie Decision Latency** : `input_tokens_to_llm` loggué séparément
   pour chaque pipeline. La différence de latence reflète la taille de l'input,
   pas uniquement la qualité du format.

3. **Silence Resilience décomposée** : INC-S2-03 (silence oracle) évaluée
   en deux sous-composantes indépendantes :
   - `detection_score` : le silence a-t-il été détecté par le pipeline ?
   - `diagnostic_score` : le diagnostic produit est-il correct vs ground truth ?

4. **INC-S2-04 spécifique à D-SIG** : la métrique Trust Accumulation Utility
   (M08) est particulièrement pertinente sur cet incident. Logger
   `baseline_cycles` à t=18h (avant) et t=19h (après rupture) pour que
   DeepSeek puisse quantifier la valeur ajoutée.

5. **Différence S1 vs S2** : noter explicitement que S2 teste le throughput
   burst (absent de S1) et le silence oracle (présent en S1 comme INC-04
   mais maintenant en position centrale dans S2).

---

## Contraintes de livraison

- Commande unique : `python scenario2/run_scenario2.py [--synthetic] [--skip-llm]`
- Aucun input interactif
- `results/scenario2/summary.csv` format identique à `results/scenario1/summary.csv`
  pour permettre à DeepSeek une comparaison directe entre scénarios
- Ne pas modifier les fichiers dans `scenario1/` sauf adaptation colonnes
  documentée avec `# SCENARIO2 ADAPTATION`
- Commit message : `feat: scenario2 - network throughput stress test`
