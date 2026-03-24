# D-SIG — Distilled Signal Standard v0.5

> *An architectural blueprint and position paper for the distillation of digital vitality signals.*  
> **Public Domain — CC0 — March 2026**

---

## What D-SIG Is

D-SIG proposes a framework — not a formula — for producing, transmitting, and consuming unified vitality signals in distributed systems.

It does not claim to compute truth. It proposes a structured way to **see and understand operational state differently**: through multi-perspective convergence, cumulative trust, and semantically rich distillation.

> Like TCP/IP does not guarantee packet delivery but maximises the probability of it through a documented protocol, D-SIG does not compute truth but maximises the probability of producing actionable operational intelligence through a documented distillation architecture.

---

## The Signal — Minimal Structure

Every D-SIG signal is a **Triple-Reduction**: three mandatory, atomically consistent representations of the same state, each targeting a distinct cognitive channel.

| Component | Form | Sign (Peirce) | Cognitive Channel |
|---|---|---|---|
| **score** | Integer 0–100 | Index | Analytical — quantitative comparison, AI consumption |
| **label** | 4 states | Symbol | Semantic — shared vocabulary across all expertise levels |
| **color** | 4 states | Icon | Limbic — pre-analytical reflex, immediate visual priority |

Plus two mandatory temporal fields:

- **trend** — temporal derivative: `STABLE | IMPROVING | DEGRADING | CRITICAL_FALL`
- **timestamp** + **ttl** — freshness validation and anti-replay

**Rule 10 (new v0.5):** label is always `f(score)`. trend is always `f(d(score)/dt)`. They are independent. A `GOOD` label with `CRITICAL_FALL` trend does not become `DEGRADED` — it remains `GOOD` with a separate urgency signal.

### Correspondence Table

| Score | Label | Color | Hex |
|---|---|---|---|
| 85–100 | EXCELLENT | GREEN | #2ECC71 |
| 60–84 | GOOD | YELLOW | #F4D03F |
| 35–59 | DEGRADED | ORANGE | #E67E22 |
| 0–34 | CRITICAL | RED | #E74C3C |

---

## Required Fields

```json
{
  "dsig_version": "0.5",
  "score": 82,
  "label": "GOOD",
  "color": "YELLOW",
  "trend": "STABLE",
  "timestamp": "2026-03-09T14:32:00Z",
  "ttl": 900,
  "source_id": "fp:a3:7c:12:...:ed25519",
  "perspective": "LOCAL"
}
```

## Recommended Fields

```json
{
  "source_sig": "base64(Ed25519_signature)",
  "source_pub": "base64(public_key_fingerprint)",
  "trust_level": 1,
  "baseline_cycles": 10,
  "dimensions": {
    "vital":      {"score": 1,  "ts": "2026-03-09T14:32:00Z", "ttl": 300},
    "local":      {"score": 10, "ts": "2026-03-09T14:31:00Z", "ttl": 3600},
    "internet":   {"score": 25, "ts": "2026-03-09T14:31:00Z", "ttl": 3600},
    "dns":        {"score": 15, "ts": "2026-03-09T14:31:00Z", "ttl": 3600},
    "throughput": {"score": 22, "ts": "2026-03-09T08:04:00Z", "ttl": 43200},
    "hub":        {"score": 10, "ts": "2026-03-09T14:32:00Z", "ttl": 600}
  },
  "flags": []
}
```

See `schema/dsig-signal.json` for the full JSON Schema validator.

---

## Five Architectural Principles

| # | Principle | Core Idea | Origin |
|---|---|---|---|
| P1 | Semantic Triple-Reduction | score + label + color are mandatory and atomically consistent | Semiology (Peirce, 1867) |
| P2 | Convergent Multi-Perspective | N independent perspectives — convergence confirms, divergence diagnoses | Distributed Systems |
| P3 | Production Autonomy | A node emits even without network. Silence is semantically charged. | Edge Resilience |
| P4 | Asymmetric Noise Absorption | Only sustained trends trigger label changes. Silence is the default state. | Signal Processing |
| P5 | Agnostic Diffusion | Any transport medium. Receiver needs no knowledge of underlying sources. | Stigmergy (Grassé, 1959) |

---

## Two Emergent Properties

**Prusik Principle** — Each additional legitimate perspective that maintains its real signal increases the visibility of divergence from falsified signals. The attack amplifies the alert it seeks to mask. Byzantine tolerance: `⌊(N−1)/3⌋` corrupted perspectives tolerated with N independent sources.

**Pheromone Principle** — Each convergence cycle deposits trust. A break after sustained convergence (high `baseline_cycles`) is statistically more significant than a break in a new deployment. Trust accumulates; it also evaporates without renewal (TTL).

---

## Distillation Formula

```
score = ( Σ wᵢ × normalize(mᵢ) ) × Π fail_fast_modifier(dⱼ) × precondition_gate(pₖ)
```

- **wᵢ** — dimension weights. Sum = 1.0. **Implementation-defined.**
- **fail_fast_modifier** — if a critical dimension = 0, score collapses toward CRITICAL (Rule 1)
- **precondition_gate** (new v0.5) — if precondition fails, score is **capped** at ≤ 20, not zeroed (Rule 11)

### Reference Profile: IT-Node (NetPulse)

| Dimension | Weight | Type | Collection |
|---|---|---|---|
| vital | PRECONDITION | precondition_gate | Every cycle |
| local | 10 pts | gradual | Every 6h |
| internet | 25 pts | binary | Every 6h |
| dns | 15 pts | binary | Every 6h |
| throughput | 35 pts | gradual | Bi-daily |
| hub | 15 pts | semi-binary | Every cycle |

Implementations MUST document their profile. Standardised profiles (Critical-Infrastructure, IoT-Edge, Cloud-Native) are planned for v1.0.

---

## Rules Summary

| Rule | Name | Version |
|---|---|---|
| 1 | Fail-Fast on Vital Dimension | v0.1 |
| 2 | Temporal Noise Smoothing | v0.1 |
| 3 | Perspective Divergence is Diagnostic | v0.1 |
| 4 | Production Autonomy | v0.1 |
| 5 | Triple-Reduction Immutability | v0.1 |
| 6 | Verifiable Source Independence (Byzantine: ⌊(N−1)/3⌋) | v0.3 |
| 7 | Contradictory Signal Rejection (incl. baseline_cycles jump) | v0.3 |
| 8 | STALE Signal / Anti-Replay (±30s clock tolerance) | v0.3 |
| 9 | Receiver-Computed Convergence History | v0.4, **revised v0.5** |
| 10 | Label/Trend Independence (label = f(score) only) | **new v0.5** |
| 11 | Precondition Dimension (cap ≤ 20, not zero) | **new v0.5** |

---

## Producer Trust Model (D-SIG-PROD)

| ID | Name | Summary |
|---|---|---|
| PROD-01 | Stable Identity | source_id = cryptographic key, not network address |
| PROD-02 | Absence Semantics | Silence is a signal, not a gap |
| PROD-03 | Assumed Co-Habitation | Control and observation share the same network by default |
| PROD-04 | Signal Authenticity Distinct from Channel | source_sig ≠ SSH authentication |
| PROD-05 | Single Anchor — Systemic Invariant | D-SIG robustness is bounded by the enrolment mechanism security |

---

## Documented Limits

1. **Over-distillation risk** — miscalibrated weights create false confidence
2. **Observer effect** — the probe perturbs what it measures (minimised, not resolved)
3. **Oracle problem** — a producer can sign valid signals with fabricated data; mitigated by multi-perspective convergence, not resolved
4. **Single anchor** — all Byzantine resistance fails if the enrolment mechanism is compromised
5. **Weighting interoperability** — two D-SIG-compliant deployments with different profiles produce non-comparable scores

---

## Intellectual Genealogy

D-SIG applies the composite indicator architecture of algorithmic trading to IT observability:

| QAAF / Trading | D-SIG | Role |
|---|---|---|
| Raw price/volume metrics | Raw network metrics | Input layer |
| Composite score (0–100) | Distilled score (0–100) | Normalised vitality |
| MACD, RSI trend signal | trend: IMPROVING / DEGRADING / CRITICAL_FALL | Temporal derivative |
| Stop-loss trigger | Fail-fast modifier | Critical threshold |
| RSI reference period | baseline_cycles | Accumulated trust proxy |
| BUY / HOLD / SELL | EXCELLENT / GOOD / DEGRADED / CRITICAL | Actionable semantic output |

---

## Governance

- **Licence:** CC0 — Public Domain. No restrictions. No certification authority.
- **Prior art:** GitHub commit timestamp + arXiv cs.NI submission
- **DOI permanent :** [10.5281/zenodo.19186972](https://doi.org/10.5281/zenodo.19186972)
  — Zenodo record, timestamped 2026-03-23, citable as prior art
- **Reference implementation:** NetPulse — copyright author, separate from this standard
- **Compatibility:** implement required fields + document your weighting profile = D-SIG compatible

---

## Repository Structure

```
dsig-standard/
├── README.md              ← Overview and quickstart
├── SPEC.md                ← This document — full specification
├── CHANGELOG.md           ← v0.1 → v0.5 history
├── LICENSE                ← CC0 full text
├── schema/
│   ├── dsig-signal.json   ← JSON Schema validator
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

*D-SIG Standard v0.5 · Public Domain CC0 · March 2026*  
*Reference implementation: NetPulse v1.7+ · github.com/dsig-standard*
