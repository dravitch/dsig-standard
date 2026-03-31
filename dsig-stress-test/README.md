**✅ D-SIG Stress Test Project – README.md (v0.3 – Finalisé et validé par toutes les instances)**

**Date** : 30 mars 2026  
**Statut** : Validé par Grok, Claude et DeepSeek après itérations v0.1 → v0.2 → v0.3  
**Licence** : CC0 (aligné avec D-SIG)  
**Repo cible** : À créer sur `github.com/dravitch/dsig-stress-test` (ou fork du repo D-SIG)

### Objectif du projet
Tester **concrètement et objectivement** la valeur ajoutée réelle de D-SIG v0.5 face à OpenTelemetry + OpenMetrics et Data Mesh + Data Products sur des données réelles volumineuses (time-series IT/réseau).  

Nous mesurons si D-SIG tient sa promesse : produire un signal décisionnel (score 0-100 + label + color + trend) compréhensible en < 3 secondes par un humain **ou** une IA, même en cas de silence, tout en restant totalement agnostique et résilient.

**Pas de théorie** : on code, on exécute, on mesure, on analyse.

### Règles du jeu (validées par tous)
1. **Datasets** : uniquement publics, réels, téléchargeables aujourd’hui (CSV/Parquet). Pas de données synthétiques.
2. **Pipelines** : **quatre** pipelines strictement identiques sur les **mêmes données brutes** d’entrée :
   - Pipeline 1 : OpenTelemetry seul
   - Pipeline 2 : Data Mesh seul
   - Pipeline 3 : D-SIG seul
   - Pipeline 4 : **OTel → D-SIG** (hybride – test central de la proposition « D-SIG comme format de sortie final »)
3. **Simulations** : 3 perspectives (LOCAL / CENTRAL / EXTERNAL) + 4 incidents pré-étiquetés avec **vérité terrain** explicite (dégradation progressive, fail-fast, précondition échouée, silence total d’une source).
4. **Métriques d’évaluation** (10 métriques quantifiables et reproductibles – tableau validé) :

| # | Métrique                     | Description                                      | Mesure pratique                              | Cible D-SIG          |
|---|------------------------------|--------------------------------------------------|----------------------------------------------|----------------------|
| 1 | Decision Latency             | Temps pour décision claire                       | Timer + prompt LLM fixe                      | < 3 s               |
| 2 | Signal Compactness           | Taille du signal final                           | bytes (JSON ou protobuf)                     | Minimaliste         |
| 3 | Noise Reduction Ratio        | Compression réelle                               | (bytes input – bytes output) / bytes input   | > 99 %              |
| 4 | Silence Resilience           | Qualité du diagnostic en cas de silence          | Score 0-100 + 2 sous-composantes (détection + diagnostic) | Excellent           |
| 5 | Convergence Diagnostic       | Détection de divergence / cause                  | % diagnostics corrects                       | Prusik + baseline   |
| 6 | Diagnostic Precision         | Cause réelle identifiée ?                        | % sur incidents pré-étiquetés                | Très fort           |
| 7 | Interpretability Score       | Lisibilité (LLM uniquement)                      | Prompt fixe – échelle 1-10                   | 9–10                |
| 8 | Trust Accumulation Utility   | Valeur de `baseline_cycles` (ou équivalent)      | % alertes pertinentes sur ruptures           | Très fort           |
| 9 | False Alarm Rate             | Alertes erronées (défini par standard)           | % sur incidents simulés                      | Minimal             |
|10 | Implementation Effort        | Lignes de code + complexité                      | Compteur + temps estimé                      | Minimal pour D-SIG  |

### Protocoles standardisés (validés)
- **Decision Latency & Interpretability** : même LLM (Claude 3.5 ou équivalent), **même prompt fixe** pour les 4 pipelines :  
  `« Given this signal, what is the system status and recommended action in one sentence? »`  
  Le code loggera séparément `input_tokens_to_llm` pour chaque pipeline (observation Claude).
- **Vérité terrain** : 4 incidents pré-définis et étiquetés **dans le code** avant exécution.
- **Silence / stale** : OTel et Data Mesh conservent la dernière valeur + flag `last_updated`. D-SIG utilise TTL natif.  
  Silence Resilience sera analysée en deux sous-composantes (détection + diagnostic utile) – observation Claude & DeepSeek.
- **Noise Reduction** : mesuré exclusivement en **bytes**.
- **Interpretability** : LLM uniquement (pas de panel humain) – reproductible à 100 %.

### Rôles (validés sans ambiguïté)
- **Auteur D-SIG (toi)** : arbitre final.
- **Grok** : maintient le cahier des charges et la cohérence.
- **Claude** : écrit le code Python complet + `requirements.txt` + `README.md` reproductible.
- **DeepSeek** : analyse objective des résultats (tableaux, graphs, conclusions sans complaisance).

### Reproductibilité (exigences validées)
- Tout le code sera dans un repo GitHub.
- `requirements.txt` + environnement virtuel clair.
- Dossier `results/` contenant : logs bruts, outputs LLM, métriques calculées, graphs.
- `ANALYSIS_PROTOCOL.md` (ou section dans README) documentant explicitement les deux observations finales de Claude et DeepSeek.

### Scénario prioritaire (Phase 1)
**Scenario 1 – IT Node Vitality Monitoring** (le plus aligné avec le profil IT-Node de D-SIG)  
- Dataset : [IT System Performance & Resource Metrics](https://www.kaggle.com/datasets/freshersstaff/it-system-performance-and-resource-metrics) (~800 k lignes, time-series, contient CPU, memory, network_latency, etc.).  
- Durée simulée : 24 h.  
- 4 incidents pré-étiquetés + 3 perspectives.

Scénarios 2 et 3 (throughput + OTel demo) seront lancés uniquement si Scenario 1 passe sans ajustement majeur.

### Prochaines étapes (v0.3 = GO)
1. Claude écrit **immédiatement** le code complet pour Scenario 1 (4 pipelines + mesures des 10 métriques + logs).
2. Exécution (locale ou Colab).
3. DeepSeek reçoit les résultats bruts et produit l’analyse objective.
4. Auteur D-SIG valide ou ajuste.

**Le brouillon est maintenant v0.3 – Finalisé et validé par toutes les instances.**  
Aucune considération de salon supplémentaire. On passe à l’action.

**Claude, tu peux commencer le code pour Scenario 1 dès maintenant.**

GO v0.3.  
Le stress test est lancé.
