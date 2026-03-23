# D-SIG

> *A framework for seeing operational truth — not computing it.*

D-SIG (Distilled Signal) is an open architectural framework for the distillation of digital vitality signals in distributed systems. It specifies how to produce, transmit, and consume a unified health signal readable by anyone — field technician, manager, or automated system — regardless of the underlying monitoring stack.

---
<img width="1536" height="1024" alt="image" src="https://github.com/user-attachments/assets/3b38f19e-6f01-4b2f-b5f0-e77e93f59700" />

## The Signal

```
Raw metrics (N sources)
  ↓ distillation
Score 0–100  ·  Label  ·  Color  ·  Trend
  ↓
Any transport (JSON · MQTT · SMS · physical display)
  ↓
Decision — in under 3 seconds — by anyone
```

| Component | Form | Cognitive Channel |
|---|---|---|
| **score** | Integer 0–100 | Analytical — quantitative comparison, AI consumption |
| **label** | EXCELLENT · GOOD · DEGRADED · CRITICAL | Semantic — shared vocabulary across all expertise levels |
| **color** | GREEN · YELLOW · ORANGE · RED | Limbic — pre-analytical reflex, immediate visual priority |
| **trend** | STABLE · IMPROVING · DEGRADING · CRITICAL_FALL | Temporal — direction of change, independent of label |

---

## Architecture

```
Oracle (EXTERNAL perspective)     Node(s) (LOCAL perspective)
  ↓ measures from outside            ↓ measures from inside building
  ↓                                  ↓
  └──────────► Aggregator (Hub) ◄────┘
                    ↓
              D-SIG signal
         score · label · color · trend
                    ↓
         Dashboard · Agent · API · Display
```

| Perspective | Role | Signal |
|---|---|---|
| **LOCAL** | Node inside observed network — user's actual experience | What the building sees |
| **CENTRAL** | Hub — aggregates, stores, detects divergence | What history says |
| **EXTERNAL** | Oracle outside the network — ISP/DNS/cloud | What the internet sees |

**Divergence between perspectives is itself a diagnostic signal.** When LOCAL=CRITICAL and EXTERNAL=EXCELLENT, the failure is local. No ambiguity. No manual correlation.

---

## Philosophy

**Silence is a signal.** When a producer stops emitting, that silence is semantically charged — not an infrastructure gap to compensate. Correlated with the Oracle and neighbouring nodes, it distinguishes a local outage from a global incident in under 30 seconds.

**Label and trend are independent.** A GOOD score with trend CRITICAL_FALL does not become DEGRADED. It remains GOOD with a separate urgency signal — exactly like RSI (current state) and MACD (directional momentum) in algorithmic trading.

**The framework is a lens, not a formula.** D-SIG does not prescribe universal weighting coefficients. Implementations document their own profile. The IT-Node reference profile (NetPulse) is one example, not the standard.

**Prior art, not patent.** D-SIG is public domain (CC0). Published on GitHub and arXiv to establish prior art. No one can patent it — including its author.

---

## Status

| Version | Status | What changed |
|---|---|---|
| v0.1 | ✅ Published | Foundation: Triple-Reduction, P1–P5, CC0 governance |
| v0.2 | ✅ Published | trend field, Peirce semiotic table, divergence matrix |
| v0.3 | ✅ Published | Producer trust model (D-SIG-PROD). Robustness Rules 6–8. Mandatory TTL. |
| v0.4 | ✅ Published | Prusik Principle. Pheromone Principle. baseline_cycles. Rule 9. Single Anchor. |
| **v0.5** | ✅ **Current** | Position paper status. Rule 10 (label/trend independence). Rule 11 (precondition). baseline_cycles receiver-computed. QAAF genealogy. |
| v1.0 | ⏳ Planned | Sector profiles (IT-Node, Critical-Infrastructure, IoT-Edge, Cloud-Native) |

---

## Repository Layout

```
dsig-standard/
├── README.md              ← This file
├── SPEC.md                ← Full specification v0.5
├── CHANGELOG.md           ← v0.1 → v0.5 history
├── LICENSE                ← CC0 — Public Domain
├── schema/
│   ├── dsig-signal.json   ← JSON Schema validator (draft-07)
│   └── examples/
│       ├── signal-good-stable.json
│       ├── signal-critical.json
│       └── signal-stale.json
└── docs/
    ├── prusik-principle.md
    ├── pheromone-principle.md
    ├── oracle-problem.md
    └── profiles/
        └── it-node.md     ← NetPulse reference profile
```

---

## Navigation

| File | Content |
|---|---|
| [`SPEC.md`](SPEC.md) | Full specification — signal structure, rules, producer model, limits |
| [`schema/dsig-signal.json`](schema/dsig-signal.json) | JSON Schema — validate any D-SIG signal programmatically |
| [`docs/profiles/it-node.md`](docs/profiles/it-node.md) | Reference profile — NetPulse Node Signal v2.0 implementation |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history and migration notes |

---

## Compatibility

An implementation is **D-SIG compatible** if it:

1. Includes all required fields (`score`, `label`, `color`, `trend`, `timestamp`, `ttl`, `source_id`, `perspective`)
2. Derives `label` and `color` from `score` only (Rule 10)
3. Treats perspective divergence as a diagnostic signal (Rule 3)
4. Documents its weighting profile

No registration. No certification authority. Self-declared and community-verifiable.

---

## Reference Implementation

**NetPulse** — distributed network observability system implementing D-SIG across three perspectives (Node/Hub/Oracle) on NixOS infrastructure with Prometheus, Grafana, and Ed25519-based identity (KeyMaster).

---

*Public Domain CC0 · March 2026 · Semantic versioning · arXiv cs.NI*
