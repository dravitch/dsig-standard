Voici les instructions complètes pour Claude Code Web.

---

## Instructions pour Claude Code — D-SIG Stress Test · Scenario 1

**Contexte :** Le repo `dsig-standard/dsig-stress-test/` existe déjà avec un README.md validé. Tu travailles dans ce dossier. Tout le code produit doit être reproductible et versionné. Tu n'as pas à interpréter l'objectif — il est défini. Tu codes, tu loggues, tu ne juges pas les résultats. L'analyse appartient à DeepSeek.

---

### Structure à créer

```
dsig-stress-test/
├── README.md                  ← existe déjà, ne pas modifier
├── requirements.txt           ← à créer
├── scenario1/
│   ├── data/
│   │   └── fetch_data.py      ← téléchargement ou génération dataset
│   ├── ground_truth.json      ← vérité terrain pré-étiquetée (AVANT les pipelines)
│   ├── pipeline_otel.py       ← Pipeline 1 : OTel seul
│   ├── pipeline_datamesh.py   ← Pipeline 2 : Data Mesh seul
│   ├── pipeline_dsig.py       ← Pipeline 3 : D-SIG seul
│   ├── pipeline_otel_dsig.py  ← Pipeline 4 : OTel → D-SIG (hybride)
│   ├── metrics.py             ← calcul des 10 métriques (partagé)
│   ├── llm_eval.py            ← évaluation LLM via Anthropic API
│   └── run_scenario1.py       ← orchestrateur principal
└── results/
    └── scenario1/
        ├── raw_outputs/       ← outputs JSON bruts des 4 pipelines
        ├── metrics_report.json ← les 10 métriques calculées
        ├── llm_responses.json  ← réponses LLM brutes
        └── summary.csv        ← tableau comparatif pour DeepSeek
```

---

### Étape 0 — Vérité terrain (ground_truth.json)

**Créer ce fichier EN PREMIER, avant tout pipeline.** Il est la référence immuable.

```json
{
  "scenario": "IT Node Vitality Monitoring",
  "dataset": "IT System Performance & Resource Metrics (Kaggle)",
  "simulation_window": "24h",
  "perspectives": {
    "LOCAL": "Node metrics — CPU, memory, latency, uptime",
    "CENTRAL": "Hub aggregation — rolling 5min averages across all nodes",
    "EXTERNAL": "Oracle — external latency proxy, internet reachability"
  },
  "incidents": [
    {
      "id": "INC-01",
      "t_start_h": 6,
      "t_end_h": 8,
      "type": "progressive_degradation",
      "cause": "EXTERNAL",
      "description": "Progressive latency increase 4ms → 180ms over 2h. LOCAL and CENTRAL still functional. Oracle degrades first.",
      "expected_diagnosis": "ISP or upstream provider degradation",
      "silent_source": null
    },
    {
      "id": "INC-02",
      "t_start_h": 10,
      "t_end_h": 10.083,
      "type": "fail_fast",
      "cause": "LOCAL",
      "description": "Vital service stops at t=10h (uptime=0, CPU=0). Immediate collapse.",
      "expected_diagnosis": "Local node vital service failure",
      "silent_source": null
    },
    {
      "id": "INC-03",
      "t_start_h": 14,
      "t_end_h": 15.5,
      "type": "silence_local",
      "cause": "LOCAL",
      "description": "LOCAL node stops emitting entirely. CENTRAL and EXTERNAL remain GREEN.",
      "expected_diagnosis": "Local hardware or network isolation. Not an ISP issue.",
      "silent_source": "LOCAL"
    },
    {
      "id": "INC-04",
      "t_start_h": 18,
      "t_end_h": 19,
      "type": "silence_oracle",
      "cause": "EXTERNAL",
      "description": "Oracle (EXTERNAL) stops emitting. LOCAL and CENTRAL nominal.",
      "expected_diagnosis": "External monitoring provider issue. Internal systems unaffected.",
      "silent_source": "EXTERNAL"
    }
  ]
}
```

---

### Étape 1 — Dataset (fetch_data.py)

Tenter le téléchargement Kaggle via `kaggle datasets download`. Si l'API Kaggle n'est pas disponible dans l'environnement, générer un dataset synthétique **qui respecte exactement le même schéma** et les mêmes statistiques décrites (800k lignes, time-series 24h, colonnes : `timestamp`, `cpu_usage`, `memory_usage`, `network_latency_ms`, `disk_io`, `process_count`, `uptime_seconds`, `node_id`).

Le dataset synthétique doit respecter ces contraintes :
- Baseline nominale : latency 3–8ms, CPU 20–60%, memory 40–70%, uptime croissant
- Les 4 incidents injectés aux timestamps de ground_truth.json
- 3 nodes distincts : `node-local-01` (LOCAL), `node-hub-01` (CENTRAL), `node-oracle-01` (EXTERNAL)
- Fréquence : 1 point par minute → 1440 points × 3 nodes = 4320 lignes minimum

Logger : `data_source = "kaggle"` ou `data_source = "synthetic_v1"` dans les résultats.

---

### Étape 2 — Les 4 pipelines

**Contrainte commune à tous :** chaque pipeline reçoit exactement les mêmes données brutes. Chaque pipeline loggue : timestamp de début, timestamp de fin, taille input en bytes, taille output en bytes, nombre de tokens envoyés au LLM.

#### Pipeline 1 — OTel seul (pipeline_otel.py)

Simuler le comportement d'OpenTelemetry + OpenMetrics :
- Produire des métriques agrégées : `latency_p50`, `latency_p99`, `cpu_avg`, `memory_avg`, `error_rate` (uptime = 0 → error)
- Format output : texte OpenMetrics standard
  ```
  node_latency_p99{node="node-local-01"} 8.2 1743000000
  node_cpu_avg{node="node-local-01"} 45.3 1743000000
  ```
- Silence : conserver la dernière valeur + ajouter label `stale="true"` après 2 cycles sans update
- Signal décisionnel pour LLM : les 5 métriques clés formatées en texte plat

#### Pipeline 2 — Data Mesh seul (pipeline_datamesh.py)

Simuler un Data Product autonome :
- Produire un JSON structuré avec métadonnées + résumé + KPIs
  ```json
  {
    "data_product_id": "node-vitality-v1",
    "domain": "infrastructure",
    "version": "1.0",
    "last_updated": "2026-03-30T06:00:00Z",
    "quality_score": 0.94,
    "kpis": {
      "latency_p99_ms": 8.2,
      "cpu_avg_pct": 45.3,
      "memory_avg_pct": 62.1,
      "error_rate_pct": 0.0,
      "uptime_pct": 99.9
    },
    "status": "NOMINAL",
    "last_known_values": {...},
    "stale": false
  }
  ```
- Silence : `stale: true`, `last_updated` conservé, `stale_duration_minutes` calculé

#### Pipeline 3 — D-SIG seul (pipeline_dsig.py)

Implémenter le profil IT-Node de D-SIG v0.5 strictement :

```python
def compute_dsig_score(metrics, prev_scores, baseline_cycles):
    # Dimensions IT-Node
    vital = 1 if metrics['uptime'] > 0 else 0  # précondition
    local = compute_local_score(metrics['latency_ms'])
    internet = compute_internet_score(metrics['packet_loss_pct'])
    dns = compute_dns_score(metrics['dns_latency_ms'])
    throughput = compute_throughput_score(metrics['throughput_mbps'], baseline)
    hub = compute_hub_score(metrics['hub_latency_ms'], metrics['scrape_age_s'])

    # Fail-fast + précondition
    if vital == 0:
        raw_score = min(20, local * 2)
    else:
        raw_score = local + internet + dns + throughput + hub

    score = min(100, max(0, int(raw_score)))
    label = score_to_label(score)       # Rule 10 : f(score) uniquement
    color = label_to_color(label)
    trend = compute_trend(prev_scores)  # Rule 10 : f(d(score)/dt)

    return {
        "dsig_version": "0.5",
        "score": score,
        "label": label,
        "color": color,
        "trend": trend,
        "timestamp": metrics['timestamp'],
        "ttl": 300,
        "source_id": metrics['node_id'],
        "perspective": metrics['perspective'],
        "baseline_cycles": baseline_cycles,
        "dimensions": {
            "vital": {"score": vital * 100, "ts": metrics['timestamp'], "ttl": 300},
            "local": {"score": local * 10, "ts": metrics['timestamp'], "ttl": 3600},
            "internet": {"score": internet, "ts": metrics['timestamp'], "ttl": 3600},
            "dns": {"score": dns, "ts": metrics['timestamp'], "ttl": 3600},
            "throughput": {"score": throughput, "ts": metrics['timestamp'], "ttl": 43200},
            "hub": {"score": hub, "ts": metrics['timestamp'], "ttl": 600}
        }
    }
```

- Silence (Rule 8) : si TTL dépassé → signal STALE avec `trend: CRITICAL_FALL`, label reste mais flag `stale: true`
- baseline_cycles : incrémenter si convergence avec les autres perspectives, reset si divergence > 30 pts

#### Pipeline 4 — OTel → D-SIG hybride (pipeline_otel_dsig.py)

- Étape 1 : produire les métriques OTel (identique Pipeline 1)
- Étape 2 : consommer ces métriques OTel comme input de la distillation D-SIG
- Logger séparément : `otel_output_bytes`, `dsig_output_bytes`, `total_pipeline_bytes`
- C'est ce pipeline qui teste la thèse "D-SIG comme dernier mile"

---

### Étape 3 — Métriques (metrics.py)

Calculer les 10 métriques pour **chaque pipeline** sur **chaque incident** :

```python
METRICS = {
    "M01_decision_latency_s": ...,        # timer LLM call
    "M02_signal_compactness_bytes": ...,  # len(json.dumps(signal))
    "M03_noise_reduction_ratio_pct": ..., # (input_bytes - output_bytes) / input_bytes * 100
    "M04_silence_resilience": {
        "detection_score": ...,           # 0-100 : silence détecté ?
        "diagnostic_score": ...,          # 0-100 : cause correctement identifiée ?
    },
    "M05_convergence_diagnostic_pct": ..., # % incidents où divergence perspect. détectée
    "M06_diagnostic_precision_pct": ...,   # % causes correctes vs ground_truth
    "M07_interpretability_score": ...,     # LLM rating 1-10
    "M08_trust_accumulation_utility": ..., # % alertes pertinentes sur baseline_cycles breaks
    "M09_false_alarm_rate_pct": ...,       # alertes erronées / total alertes
    "M10_implementation_effort_loc": ...,  # wc -l pipeline_*.py
}
```

Pour M09, définir "fausse alarme" par standard :
- OTel : seuil franchi sans incident réel dans ground_truth.json
- Data Mesh : `status != "NOMINAL"` sans incident réel
- D-SIG : label DEGRADED ou CRITICAL sans incident réel

---

### Étape 4 — Évaluation LLM (llm_eval.py)

Utiliser l'API Anthropic (claude-sonnet-4-6) :

```python
PROMPT_FIXED = "Given this signal, what is the system status and recommended action in one sentence?"

def evaluate_signal(signal_text, pipeline_name):
    start = time.time()
    response = anthropic_client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=100,
        messages=[{"role": "user", "content": f"{PROMPT_FIXED}\n\nSignal:\n{signal_text}"}]
    )
    latency = time.time() - start
    return {
        "pipeline": pipeline_name,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_s": latency,
        "response": response.content[0].text,
        "interpretability_rating": extract_rating(response.content[0].text)
        # demander au LLM de s'auto-noter : ajouter au prompt "Rate clarity 1-10."
    }
```

Appeler pour chaque pipeline à chaque incident (4 incidents × 4 pipelines = 16 appels).

---

### Étape 5 — Orchestrateur (run_scenario1.py)

```python
# 1. Load ground truth
# 2. Fetch/generate data
# 3. Run all 4 pipelines
# 4. For each pipeline × each incident :
#    - Extract signal at incident timestamp
#    - Call LLM
#    - Compute all 10 metrics
# 5. Write results/scenario1/
#    - raw_outputs/*.json
#    - metrics_report.json
#    - llm_responses.json
#    - summary.csv (rows=pipelines, cols=metrics)
# 6. Print: "Scenario 1 complete. Results in results/scenario1/"
```

---

### Étape 6 — requirements.txt

```
pandas>=2.0
numpy>=1.24
anthropic>=0.20
kaggle>=1.6        # optionnel, fallback synthétique si absent
python-dateutil
```

---

### Contraintes de livraison

- Le code doit tourner en une seule commande : `python scenario1/run_scenario1.py`
- Aucun input interactif requis
- `results/scenario1/summary.csv` doit être lisible directement par DeepSeek
- Chaque pipeline est dans son propre fichier — pas de monolithe
- Commenter chaque décision non-triviale (surtout les formules de distillation D-SIG)
- `ANALYSIS_PROTOCOL.md` à créer dans `results/scenario1/` documentant les deux points d'asymétrie : (1) `input_tokens_to_llm` loggué séparément, (2) Silence Resilience décomposée en deux sous-composantes

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
