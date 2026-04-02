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
