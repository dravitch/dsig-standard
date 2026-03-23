---
title: "D-SIG: Distilled Signal Standard — An Architectural Blueprint for Digital Vitality Signals"
author: "Andrei Dinga-Reassi"
date: "March 2026"
version: "0.5"
status: "Position Paper — Open for Community Review"
license: "CC0 1.0 Universal"
arxiv:
  subject: "cs.NI"
  secondary: "cs.DC"
  comments: "27 pages, JSON schema in appendix. Reference implementation: NetPulse (github.com/dsig-standard). Public domain CC0."
---

\newpage

## Abstract

**Context.** Modern observability systems collect vast amounts of data but degrade
teams' decision capacity. The Observability Paradox — more data, less insight —
remains unresolved by current tools, which provide raw data without operational
semantics.

**Contribution.** This paper presents D-SIG v0.5, an open architectural blueprint
for distilling digital vitality signals in distributed systems. It specifies a
Triple-Reduction signal (normalised score 0–100, semantic label, colour code, and
temporal trend) and two emergent robustness properties: the Prusik Principle
(self-reinforcing Byzantine resistance through perspective independence) and the
Pheromone Principle (cumulative trust through convergence history, formalised in
the `baseline_cycles` field).

**Properties.** The framework defines five architectural principles (P1–P5), eleven
distillation and robustness rules, and a producer trust model (D-SIG-PROD-01–05).
All weighting parameters are implementation-defined. A reference profile (IT-Node)
is provided via the NetPulse implementation. D-SIG is a compositional innovation
through interdisciplinary transfer, applying composite indicator architectures from
algorithmic trading (RSI, MACD) to IT observability.

**Limits.** D-SIG does not solve the oracle problem (proof of measurement) or the
single-anchor invariant (enrolment security). These limits are explicitly
documented. This paper is a position paper, not a prescriptive standard, and is
released under CC0.

---

## Acknowledgements

This work was developed with the assistance of Claude (Anthropic) as a
collaborative reasoning tool for specification design and peer review. The
intellectual contributions, design decisions, and responsibility for the content
are those of the author.

---

## Version History

| Version | Date | Key Changes |
|---------|------|-------------|
| v0.1 | Mar 2026 | Foundation: Triple-Reduction, P1–P5, multi-perspective distillation, CC0 governance. |
| v0.2 | Mar 2026 | velocity → trend, Peirce semiotic table, divergence matrix. |
| v0.3 | Mar 2026 | Producer trust model D-SIG-PROD-01–04. Robustness Rules 6–8. Mandatory TTL. |
| v0.4 | Mar 2026 | Prusik Principle. Pheromone Principle. baseline_cycles. Rule 9. D-SIG-PROD-05. |
| **v0.5** | **Mar 2026** | **Position paper status. Rule 10 (label/trend independence). Rule 11 (precondition). baseline_cycles receiver-computed. QAAF genealogy. Generic scenario.** |

---

## 1. Intellectual Genealogy and Motivation

### 1.1 From Algorithmic Trading to IT Observability

D-SIG did not emerge from the IT observability domain. It emerged from a
structural observation made by a practitioner of algorithmic trading who also
operated distributed network infrastructure: the signal processing patterns that
work in financial markets — composite indicators, trend derivatives, convergence
of independent perspectives — had never been formally applied to IT operational
monitoring.

The QAAF framework (Quantitative Algorithmic Asset Framework) — a composite
scoring system for PAXG/BTC asset allocation based on momentum, volatility, and
correlation metrics — provided the structural template:

| QAAF (Algorithmic Trading) | D-SIG (IT Observability) | Structural Role |
|----------------------------|--------------------------|-----------------|
| Raw price/volume metrics | Raw network metrics (latency, loss, throughput) | Input layer — unprocessed observations |
| Composite score (0–100) | Distilled score (0–100) | Normalised vitality signal |
| MACD, RSI, momentum | trend: IMPROVING / DEGRADING / CRITICAL_FALL | Temporal derivative of the composite |
| Stop-loss trigger | fail_fast_modifier = 0 | Critical threshold that collapses the score |
| RSI reference period | baseline_cycles | Accumulated convergence cycles as trust proxy |
| BUY / HOLD / SELL | EXCELLENT / GOOD / DEGRADED / CRITICAL | Actionable semantic output |
| Multi-indicator convergence | Multi-perspective convergence (Node/Hub/Oracle) | Independent signal confirmation |

> **Genealogy.** D-SIG is a compositional innovation through interdisciplinary
> transfer: it applies the signal processing architecture of algorithmic trading
> composite indicators to distributed IT observability, a domain where this
> formalisation was absent. QAAF is the conceptual ancestor; D-SIG is the
> structural generalisation.

### 1.2 The Observability Paradox

Modern observability systems have reached a structural limit: their capacity to
collect data has grown exponentially, but the capacity of teams to transform that
flow into operational decisions has degraded in proportion. The more probes added,
the more noise produced. The more noise, the more critical signals are buried.

D-SIG proposes a different question: instead of asking *what is happening*, ask
*whether the system is fulfilling its mission for the end user, right now*. That
shift in question changes what needs to be measured — and how.

> **The problem in one sentence.** Existing tools sell data. D-SIG proposes a
> framework for producing operational truth. These are not the same product.

### 1.3 The Gap in Existing Standards

| Domain | Distilled Signal | Multi-perspective | Autonomous | IT? |
|--------|------------------|-------------------|------------|-----|
| Medical Triage (START) | Colour tags G/Y/R/B | Yes | Yes | No |
| Aviation (artificial horizon) | Synthesised fused posture | Partial | Yes | No |
| Safety/Industry (IEC 61508) | SIL levels 1–4 | Partial | Yes | No |
| IT Monitoring (Datadog, etc.) | None — raw data only | Partial | No | Yes → GAP |
| D-SIG v0.5 | Score+Label+Colour+Trend+Cumulative Trust | Yes (N perspectives) | Yes | Yes → FILLS THE GAP |

---

## 2. Nature of the Framework

### 2.1 What D-SIG Is Not

- D-SIG is not a monitoring tool. It does not collect data.
- D-SIG is not a machine learning algorithm. It requires no training.
- D-SIG is not a universal formula with fixed coefficients. Weights are implementation-defined.
- D-SIG is not a patentable invention. It is a compositional framework in the public domain.
- D-SIG is not a prescriptive standard. It is an architectural blueprint open to community refinement.

### 2.2 What D-SIG Proposes

D-SIG proposes a framework — a structured way of seeing and understanding the
operational state of a distributed system. Like TCP/IP does not guarantee packet
delivery but maximises the probability of it through a documented protocol, D-SIG
does not compute truth but maximises the probability of producing actionable
operational intelligence through a documented distillation architecture.

> **Core claim.** D-SIG proposes that: (1) a score + label + colour + trend is
> sufficient for any operational decision if correctly calibrated; (2) three
> independent perspectives are more epistemically robust than one precise
> perspective; (3) the history of convergence is itself a signal. These are
> propositions, not axioms. They are falsifiable.

### 2.3 The Five Founding Architectural Principles

| # | Principle | Description | Origin |
|---|-----------|-------------|--------|
| P1 | Semantic Triple-Reduction | Every D-SIG signal simultaneously expresses a number (0–100), a label (4 states), and a colour. All three mandatory and atomically consistent. | Semiology (Peirce, 1867) |
| P2 | Convergent Multi-Perspective | The final signal emerges from the confrontation of N independent perspectives. Convergence confirms. Divergence diagnoses. | Distributed Systems |
| P3 | Production Autonomy | Each entity produces its signal without network dependency. A failing network produces a signal — it does not suppress it. | Edge Resilience / Aviation |
| P4 | Asymmetric Noise Absorption | Micro-variations are absorbed into the score. Only a sustained trend or perspective divergence triggers a label change. Silence is the default state. | Signal Processing / HSE |
| P5 | Agnostic Diffusion | A D-SIG signal travels over any medium (JSON, MQTT, SMS, physical indicator). The receiver does not need to know the underlying sources. | Stigmergy (Grassé, 1959) |

### 2.4 Two Emergent Properties of Distributed Architecture

**Prusik Principle — Self-Reinforcing Resistance.**
A self-locking knot does not resist load through external rigidity — the load
itself tightens the grip. In a multi-perspective D-SIG deployment, each additional
legitimate perspective that maintains its real signal increases the visibility of
divergence with falsified signals. The attack amplifies the alert signal it seeks
to mask. Resistance to manipulation is a self-reinforcing function of the number
of active independent perspectives. Byzantine tolerance: a deployment with N
independent perspectives tolerates floor((N-1)/3) simultaneously corrupted perspectives.

**Pheromone Principle — Cumulative Trust Through Temporal Convergence.**
In an ant colony, short paths reinforce faster because ants deposit pheromones
more frequently. No central decision — an emergent property of repetition. Each
cycle where independent perspectives converge is a pheromone deposit, reinforcing
the trust baseline of that group. A sudden divergence after sustained convergence
(high `baseline_cycles`) is statistically more significant than a divergence in a
system without history. Signal legitimacy is not binary — it accumulates through
coherent convergence and evaporates without renewal (TTL).

### 2.5 Academic Positioning

| Information Theory (Shannon, 1948) | Semiology (Peirce, 1867) |
|------------------------------------|--------------------------|
| D-SIG distillation is controlled entropy reduction: N raw metrics → 1 score + 1 label + 1 colour, without loss of decision-relevant information. | Triple-Reduction maps to three sign types: Number = Index (analytical), Label = Symbol (semantic), Colour = Icon (limbic reflex). Redundancy is semiotic, not aesthetic. |
| **Byzantine Fault Tolerance (Lamport et al., 1982)** | **Stigmergy (Grassé, 1959)** |
| The Prusik Principle transposes Byzantine fault tolerance to observability. A D-SIG deployment with N independent perspectives tolerates floor((N-1)/3) simultaneously corrupted perspectives. | The Pheromone Principle is an instance of stigmergy: coordination emerges from traces in the environment, not direct communication. `baseline_cycles` is the formalisation of this trace. |

---

## 3. Formal Specification D-SIG v0.5

### 3.1 The Triple-Reduction — Semiotic Foundation

| Component | Technical Form | Sign (Peirce) | Cognitive Channel | Primary Use |
|-----------|----------------|---------------|-------------------|-------------|
| **THE NUMBER** | Integer 0–100 | Index | Analytical cortex — quantitative processing, temporal comparison, algorithmic storage | Retrospective analysis, trend computation, AI consumption |
| **THE LABEL** | Single word — 4 states | Symbol | Semantic comprehension — shared vocabulary across all expertise levels | Inter-level communication, reporting, management decision |
| **THE COLOUR** | Colour code — 4 states | Icon | Limbic brain — pre-analytical reflex, immediate visual priority | Dashboard, emergency detection under stress |

> **Golden Rule.** The Number, Label, and Colour are an atomic unit consistent
> with §3.3. A signal with label EXCELLENT and colour RED is invalid and MUST be
> rejected by any compliant receiver.

### 3.2 Complete D-SIG v0.5 Signal Structure

| Field | Type | Status | Description |
|-------|------|--------|-------------|
| score | integer [0–100] | REQUIRED | Normalised vitality. 100 = optimal, 0 = total failure. |
| label | enum string | REQUIRED | EXCELLENT \| GOOD \| DEGRADED \| CRITICAL. Derived from score only (Rule 10). |
| color | enum string | REQUIRED | GREEN \| YELLOW \| ORANGE \| RED. Consistent with label. |
| trend | enum string | **REQUIRED** | STABLE \| IMPROVING \| DEGRADING \| CRITICAL_FALL. Independent of label (Rule 10). |
| timestamp | ISO 8601 | REQUIRED | Production timestamp. Anti-replay and temporal analysis. |
| ttl | integer (s) | **REQUIRED** | Validity duration. Recommended max: 600s. Beyond: STALE. |
| source_id | string | REQUIRED | Stable identifier anchored on a persistent cryptographic key. NOT an ephemeral network address. |
| perspective | enum string | REQUIRED | LOCAL \| CENTRAL \| EXTERNAL |
| source_sig | string | RECOMMENDED | Ed25519 signature of payload (base64). Required for trust_level >= 1. |
| source_pub | string | RECOMMENDED | Fingerprint of producer's public key. |
| trust_level | integer | RECOMMENDED | 0 (unsigned) \| 1 (Ed25519) \| 2 (mTLS org CA) \| 3 (delegated D-SIG CA) |
| baseline_cycles | integer | **RECOMMENDED** | Receiver-computed count of consecutive convergence cycles. Producer MAY include synchronisation hint. Receiver MUST compute independently. Discontinuous jump → Rule 7. |
| dimensions | object | RECOMMENDED | Intermediate scores by dimension. Each entry SHOULD include score, timestamp, and ttl. |
| flags | array of strings | OPTIONAL | Signal-level flags: CALIBRATING, TERRAIN_STALE, HUB_UNREACHABLE, etc. |

**JSON example — D-SIG v0.5 compliant:**

\needspace{28\baselineskip}
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
  "source_sig": "base64(Ed25519_signature_of_payload)",
  "source_pub": "base64(public_key_fingerprint)",
  "trust_level": 1,
  "baseline_cycles": 10,
  "perspective": "LOCAL",
  "dimensions": {
    "vital":      {"score": 1,  "ts": "2026-03-09T14:32:00Z", "ttl": 300},
    "local":      {"score": 10, "ts": "2026-03-09T14:31:00Z", "ttl": 3600},
    "internet":   {"score": 25, "ts": "2026-03-09T14:31:00Z", "ttl": 3600},
    "dns":        {"score": 15, "ts": "2026-03-09T14:31:00Z", "ttl": 3600},
    "throughput": {"score": 22, "ts": "2026-03-09T08:04:00Z", "ttl": 43200},
    "hub":        {"score": 10, "ts": "2026-03-09T14:32:00Z", "ttl": 600}
  }
}
```

### 3.3 Triple-Reduction Correspondence Table

| Score | Label | Colour | Hex | Operational Interpretation |
|-------|-------|--------|-----|----------------------------|
| 85–100 | EXCELLENT | GREEN | #2ECC71 | No action. System fulfilling its mission at full capacity. |
| 60–84 | GOOD | YELLOW | #F4D03F | Normal monitoring. Observe trend. No intervention required. |
| 35–59 | DEGRADED | ORANGE | #E67E22 | Action recommended. Inspect dimensions field. |
| 0–34 | CRITICAL | RED | #E74C3C | Immediate action required. Incident probable or confirmed. |

*Label and colour are always derived from score. A GOOD score with trend CRITICAL_FALL does not become DEGRADED — it remains GOOD with a separate urgency signal. See Rule 10.*

### 3.4 Distillation Formula and Reference Profile

```
score = ( sum_i( w_i * normalize(m_i) ) ) × prod_j( fail_fast_modifier(d_j) ) × precondition_gate(p_k)
```

- **w_i** — dimension weights, sum = 1.0. Implementation-defined.
- **normalize(m_i)** — map raw metric to [0, 1]. Implementation-specific per dimension.
- **fail_fast_modifier(d_j)** — if critical dimension d_j = 0, modifier = 0: score collapses to CRITICAL regardless of other dimensions.
- **precondition_gate(p_k)** *(new v0.5)* — if precondition p_k = 0, score is capped at <= 20 (CRITICAL ceiling, not zero). Other dimensions contribute information within that ceiling.

**Reference Profile: IT-Node (NetPulse)**

| Dimension | Weight | Type | Collect Freq. | Description |
|-----------|--------|------|---------------|-------------|
| vital | PRECONDITION | precondition_gate | Every cycle | NetPulse services running + IP assigned. If false: score <= 20. |
| local | 10 pts | gradual | Every 6h | Gateway reachable via ping. Distinguishes node vs ISP failure. |
| internet | 25 pts | binary | Every 6h | 8.8.8.8 AND 1.1.1.1 reachable. Double target = resilience. |
| dns | 15 pts | binary | Every 6h | DNS resolution via local resolver AND direct. |
| throughput | 35 pts | gradual | Bi-daily 04:00+16:00 | iPerf3 vs 30-day P50 baseline. Upload weighted 60%. |
| hub | 15 pts | semi-binary | Every cycle | Hub reachable + scrape age. Correlates with internet for diagnosis. |

*If iPerf server unreachable, throughput weight redistributed to internet. Calibration: 9+ samples needed; below that, neutral score + CALIBRATING flag.*

### 3.5 Distillation and Robustness Rules

**Foundation Rules (v0.1–v0.3)**

1. **Fail-Fast on Vital Dimension** — if critical dimension = 0, score collapses to <= 20 regardless of all others.
2. **Temporal Noise Smoothing** — micro-variations (< 120s) do not change label. Sustained trend or > 15-point shift triggers label change.
3. **Perspective Divergence is a Diagnostic Signal** — divergence > 30 points is informational. See matrix below.
4. **Production Autonomy** — producer MUST emit signal even without network. Offline signal is valid and timestamped.
5. **Triple-Reduction Immutability** — score, label, colour form atomic unit. Contradiction invalidates signal.

**Perspective Divergence Diagnostic Matrix:**

| NODE (Local) | ORACLE (External) | HUB (Historical) | Immediate Diagnosis |
|---|---|---|---|
| CRITICAL | EXCELLENT | GOOD | Local site failure. Internet works elsewhere. |
| CRITICAL | CRITICAL | DEGRADED | External failure. ISP or regional infrastructure. |
| GOOD | DEGRADED | EXCELLENT | External degradation underway. Site holding. |
| DEGRADED | GOOD | CRITICAL | Regression vs history. Check recent changes. |
| EXCELLENT | EXCELLENT | EXCELLENT | Positive convergence. Justified silence. No action. |

**Robustness Rules (v0.3 — anti-spoofing, anti-replay)**

6. **Verifiable Source Independence** — do not treat convergence as reinforced if sources share the same signing key, network infrastructure, or deployment operator. Byzantine tolerance: floor((N-1)/3) corrupted perspectives tolerated.
7. **Contradictory Signal Rejection** — if same source_id emits two signals within TTL window with divergence > 30 points, suspend source and emit CRITICAL alert. Discontinuous `baseline_cycles` jump treated identically.
8. **STALE Signal / Anti-Replay** — if timestamp + ttl < now, treat as UNKNOWN / trend CRITICAL_FALL. Clock skew tolerance ±30s.

**Cumulative Trust Rule (v0.4, revised v0.5)**

9. **Receiver-Computed Convergence History** — receiver MUST compute `baseline_cycles` independently from its own observation history. Producer's value is a synchronisation hint only.

| baseline_cycles | Interpretation | Epistemic Weight | Pheromonal Analogy |
|-----------------|----------------|------------------|--------------------|
| 0 | First emission or recent break | Neutral | Ant on unknown path |
| 1–100 | Recent convergence, short duration | Moderate | Partially marked path |
| 101–1000 | Established convergence (hours–days) | Strong | Reinforced path |
| > 1000 | Long-duration convergence | Very strong | Pheromone highway |
| RESET | Recent divergence detected | Back to 0 | Pheromone evaporation |

**New Rules (v0.5)**

10. **Label/Trend Independence** — label = f(score) only. trend = f(d(score)/dt) only. Orthogonal signals. GOOD + CRITICAL_FALL remains GOOD with independent urgency. Mirrors RSI (current state) and MACD (directional momentum) in algorithmic trading.

| Score | Label | Trend | Correct Interpretation |
|-------|-------|-------|------------------------|
| 84 | GOOD | CRITICAL_FALL | Currently good but deteriorating rapidly. Intervene now. |
| 36 | DEGRADED | IMPROVING | Degraded but recovering. Monitor, do not escalate. |
| 62 | GOOD | STABLE | Normal monitoring. |
| 20 | CRITICAL | IMPROVING | Critical but recovering. Immediate action still required. |

11. **Precondition Dimension** — failed precondition (value = 0) caps score at <= 20, does not zero it. Other dimensions contribute within that ceiling, preserving diagnostic information. Distinct from fail-fast: a failed precondition bounds the score; a failed vital dimension collapses it.

### 3.6 Individual Dimension Freshness (new v0.5)

Dimensions have different collection frequencies. The `dimensions` field SHOULD include per-dimension timestamps and TTL values for independent freshness assessment.

| Dimension Type | Typical Collect Freq. | Suggested TTL | Staleness Behaviour |
|---|---|---|---|
| Precondition (vital) | Every cycle | = signal TTL | Stale vital → treat as failed precondition |
| Connectivity (local, internet, dns) | Every 6h | 3600–21600s | Use last known + DIMENSION_STALE flag |
| Throughput (iPerf) | Bi-daily | 43200s (12h) | Neutral score contribution + CALIBRATING flag |
| Hub connectivity | Every cycle | = signal TTL | Stale → treat as hub unreachable |

### 3.7 Producer Trust Model (D-SIG-PROD)

| Principle | Name | Definition |
|-----------|------|------------|
| PROD-01 | Stable Identity | source_id = persistent cryptographic key, not network address. Identity MUST NOT be tied to replaceable hardware (NIC, MAC) or ephemeral address (DHCP IPv4). |
| PROD-02 | Absence Semantics | Absence of signal is valid information. MUST be treated as justified silence, not infrastructure error. |
| PROD-03 | Assumed Co-Habitation | Control and observation planes share the same network by default. Deviation toward privileged transport MUST be documented. |
| PROD-04 | Signal Authenticity Distinct from Channel | SSH/TLS authentication does not guarantee that metrics originate from the declared observation point. source_sig is a separate mechanism. |
| PROD-05 | Single Anchor — Systemic Invariant | D-SIG Byzantine robustness is bounded by enrolment mechanism security. A producer enrolled through a compromised mechanism is indistinguishable from a legitimate one. Explicitly delegated to implementation. |

### 3.8 Compliant Receiver Requirements

1. Verify Triple-Reduction consistency per §3.3. MUST reject inconsistent signals.
2. Verify timestamp + ttl > now. MUST reject or mark STALE. Clock skew ±30s.
3. If source_sig present and trust_level >= 1: verify Ed25519 signature. MUST reject invalid.
4. Apply Rule 6: MUST NOT treat convergence as reinforced if sources not verifiably independent.
5. Apply Rule 7: MUST suspend sources with contradictory signals or discontinuous baseline_cycles.
6. Apply Rule 8: MUST treat STALE signals as UNKNOWN / trend CRITICAL_FALL.
7. Apply Rule 9: MUST compute baseline_cycles independently. SHOULD weight epistemic value accordingly.
8. Apply Rule 10: MUST interpret label and trend as independent signals.
9. Apply Rule 11: MUST treat precondition failure as score ceiling <= 20, not zero.
10. SHOULD expose dimension-level freshness where dimensions include timestamps and TTL.

---

## 4. Value Proposition

### 4.1 A Framework for Seeing Differently

The primary value of D-SIG is not computational — it is perceptual. It proposes a
way of seeing operational state simultaneously readable by a field technician
(colour, 3-second decision), a manager (label, no technical vocabulary required),
and an AI agent (number + trend + dimensions, structured input for autonomous
reasoning).

This multi-register readability is achieved by the Triple-Reduction architecture,
which preserves all information at different levels of abstraction simultaneously.
No information is lost between raw dimensions and distilled label; it is only
expressed differently.

### 4.2 Illustrative Scenario — Cascading Degradation

Consider a network monitoring deployment with two nodes (LOCAL perspective), one
hub (CENTRAL), and one oracle (EXTERNAL). At 14:32, the following signals are
received:

| Producer | Score | Label | Trend | baseline_cycles | Diagnosis |
|----------|-------|-------|-------|-----------------|-----------|
| Node M-20 | 78 | GOOD | DEGRADING | 1200 | Degrading from established baseline — local investigation warranted |
| Node M-24 | 81 | GOOD | STABLE | 890 | Stable — not the source |
| Oracle | 72 | GOOD | DEGRADING | 2400 | External degradation confirmed — ISP or upstream |
| Hub | AGG. | — | — | — | M-20 and Oracle both degrading → external cause probable. M-24 stable confirms not site-wide. |

Recommended action: contact ISP, not field intervention. This diagnosis emerges in
under 30 seconds without technical knowledge of network topology. The
`baseline_cycles` values make the break statistically significant: two long-history
sources diverging simultaneously is a pheromonal signal independent of absolute
score values.

### 4.3 Cumulative Trust as an Operational Asset

The `baseline_cycles` field formalises a property operational teams know
intuitively but had no structured way to express: a system stable for 72 hours
breaking at 14:32 is a different class of event from a system unstable for 3
cycles. Score + trend + baseline_cycles provides three orthogonal readings:
current state, direction of change, and historical weight of the break.

---

## 5. Ecosystem Positioning

| Solution | What It Produces | Relationship to D-SIG | Retained Value |
|----------|------------------|------------------------|----------------|
| Datadog / New Relic | Metrics + Logs + Traces | Raw data provider → D-SIG input | Forensic depth post-incident |
| Prometheus / Grafana | Time-series metrics | Native D-SIG transport + baseline_cycles storage | Persistence + visualisation |
| SolarWinds | Device status (UP/DOWN) | Binary provider → one D-SIG dimension | Network inventory |
| Uptime Kuma / OpenStatus | Service status (binary) | Binary provider → one D-SIG dimension | Simple accessible monitoring |
| NetPulse | Distilled multi-perspective signal | D-SIG reference implementation (IT-Node profile) | Distillation + resilience + KeyMaster |

---

## 6. Critical Analysis and Limits

*An intellectually honest framework documents its own limits with the same rigour
as its properties.*

### 6.1 Over-Distillation Risk

Reducing a complex system to a score of 0 to 100 carries real risk: a poorly
calibrated weighting profile can bury a critical but subtle failure in the mass of
healthy dimensions. A miscalibrated D-SIG implementation is more dangerous than
noisy monitoring — it creates false confidence while appearing rigorous.

Mitigations: Rules 1 and 11 protect critical structural conditions. The
`dimensions` field allows first-level inspection. The `trend` exposes dynamics
even when the absolute score appears acceptable. But these mechanisms are only as
good as the weighting profile that underlies them.

### 6.2 The Observer Effect

D-SIG does not resolve the observer problem — it minimises it. A Node consumes
CPU, generates network traffic, and may itself introduce the latencies it measures.
Co-habitation of control and observation planes (D-SIG-PROD-03) is a deliberate
design choice preserving user perspective fidelity at the cost of minimal
perturbation (~200 bytes of JSON vs megabytes of raw streams).

> **Fundamental limit.** D-SIG is a framework for uncertainty reduction, not
> elimination. It produces operational truth sufficient to act — not absolute truth.

### 6.3 The Oracle Problem — The Physical Contact Point

D-SIG's deepest structural limit: a producer can sign a valid signal whose data
was never measured. The cryptographic chain is impeccable from inside, but D-SIG
postulates that its producers measure something — it has no mechanism to prove
that a score was computed from real observations rather than written into a file.

| System | Oracle Problem | Resolution |
|--------|----------------|------------|
| Blockchain (Ethereum) | Smart contracts cannot verify real-world data. | Decentralised oracle protocols (Chainlink). High cost. Not transposable. |
| Bitcoin | N/A — Proof of Work is the physical anchor. | PoW makes block simulation physically costly. Not transposable. |
| D-SIG | Producer can sign valid signal with fabricated data. | Independent multi-perspective convergence (Rule 6 + Prusik Principle). Statistical and architectural, not cryptographic. |

> **Epistemological response.** D-SIG does not resolve the oracle problem. It
> minimises it: three independent sources cannot simultaneously fabricate the same
> lie without eventual divergence revealing it. This is the functional equivalent
> of proof of measurement — statistical, not cryptographic.

### 6.4 The Single Anchor — The Unresolved Invariant

All Byzantine resistance of D-SIG rests on the verifiable independence of
producers. This independence is guaranteed by the enrolment mechanism. If that
mechanism is compromised, a fraudulent producer is indistinguishable from a
legitimate one — real key, real growing `baseline_cycles`, real signed signals,
fabricated data.

This is not a weakness to hide. It is the architectural constraint that any
deployment MUST treat as its highest security priority. D-SIG explicitly delegates
protection of the enrolment mechanism to the implementation. NetPulse responds
with KeyMaster Tiers 0–3.

### 6.5 The Weighting Profile Problem

D-SIG deliberately does not prescribe universal weights. This creates an
interoperability risk: two D-SIG-compliant deployments with different profiles
produce structurally identical but semantically incomparable signals. Implementations
MUST document their weighting profile and SHOULD publish it as a named
configuration. Standardised profiles (IT-Node, Critical-Infrastructure, IoT-Edge,
Cloud-Native) are planned for v1.0.

### 6.6 Cultural Resistance

Proposing a system that privileges silence may be perceived as a loss of control
by teams that measure their expertise by their ability to read complex metrics.
The strategic response: D-SIG does not replace existing tools — it adds a
readability layer above them. Technical depth remains accessible below the signal.

---

## 7. Governance — Open Manifesto Model

1. Public GitHub repository, CC0 licence. Commit timestamp = incontestable prior art.

2. Whitepaper submission to arXiv (cs.NI). Timestamped, indexed, permanent.

3. Author retains copyright on the NetPulse reference implementation, independently of the public domain framework.

4. Any implementation declares D-SIG compatible if it respects the required fields (Section 3.2), distillation rules (Section 3.5), receiver requirements (Section 3.8), and documents its weighting profile.

5. No certification authority. Compliance is self-declared and community-verifiable.

6. Community feedback is invited on: weighting profiles for v1.0 sector standards, formalisation of precondition semantics, `baseline_cycles` computation algorithms.

> **Principle.** D-SIG belongs to the public domain. No one can patent it — including
> its author. Its protection is its published prior art and its community of
> implementers — the same mechanism that protects Linux, TCP/IP, and HTTP.

---

## 8. Conclusion

D-SIG v0.5 is the first version of the framework to fully embrace its nature as a
position paper rather than a prescriptive standard. This is not a retreat from
ambition — it is a more precise statement of what D-SIG actually claims.

The claim is this: that the combination of semantic distillation, multi-perspective
convergence, temporal trust accumulation, and documented limits produces a
framework for operational intelligence that is simultaneously more readable, more
resilient, and more honest than the monitoring paradigms it complements.

The intellectual genealogy is now documented: from algorithmic trading composite
indicators (QAAF), through the structural observation that the same pattern had
never been formalised for IT observability, to D-SIG. The transfer is
interdisciplinary, documented, and verifiable.

v0.5 closes three inconsistencies open since v0.3: label and trend are now formally
independent (Rule 10), `baseline_cycles` is now receiver-computed with the
producer's value as a synchronisation hint only (Rule 9 revised), and the
precondition dimension is now a distinct concept from fail-fast (Rule 11). These
are not cosmetic changes — they are the difference between a framework that can be
correctly implemented and one that cannot.

> Other tools look for the needle in the haystack by adding ever more hay.
> **D-SIG burns the hay.** Not because it has a better formula for finding needles.
> **Because it proposes a different way of seeing what the hay is hiding.**

---

## References

- Peirce, C.S. (1867). *On a New List of Categories*. Proceedings of the American Academy of Arts and Sciences.
- Shannon, C.E. (1948). *A Mathematical Theory of Communication*. Bell System Technical Journal.
- Grassé, P.P. (1959). *La reconstruction du nid et les coordinations inter-individuelles*. Insectes Sociaux. [Stigmergy]
- Lamport, L., Shostak, R., & Pease, M. (1982). *The Byzantine Generals Problem*. ACM Transactions on Programming Languages and Systems (TOPLAS).
- von Bertalanffy, L. (1968). *General System Theory*. George Braziller.
- Brewer, E.A. (2000). *Towards Robust Distributed Systems (CAP Theorem)*. PODC Keynote.
- Nakamoto, S. (2008). *Bitcoin: A Peer-to-Peer Electronic Cash System*.
- Dorigo, M., & Gambardella, L.M. (1997). *Ant colony system*. IEEE Transactions on Evolutionary Computation.
- Wilder, J.W. (1978). *New Concepts in Technical Trading Systems*. [RSI — conceptual ancestor of `baseline_cycles`]
- Appel, G. (1979). *The Moving Average Convergence/Divergence Method*. [MACD — conceptual ancestor of `trend` field]
- IEC 61508 — *Functional Safety of Electrical/Electronic/Programmable Electronic Safety-related Systems*.
- Forrester Research (2020). *SOC Alert Volume Study* (white paper).
- IBM / Morning Consult (2023). *SOC Performance and Alert Fatigue Survey*.
- Trend Micro (2023). *Report on SOC Analyst Alert Fatigue*.
- ACM Computing Surveys (2024). *Alert Fatigue in Security Operations Centres: Research Challenges and Opportunities*.
- Devo Technology (2024). *SOC Performance Report*.
- SANS Institute (2025). *Detection and Response Survey*.
- Verizon (2025). *Data Breach Investigations Report (DBIR)*.

---

## Appendix: JSON Schema (dsig-signal.json)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/dsig-standard/dsig-signal/v0.5/dsig-signal.json",
  "title": "D-SIG Signal",
  "description": "Distilled Signal Standard v0.5 — Public Domain CC0.",
  "type": "object",
  "required": [
    "dsig_version", "score", "label", "color", "trend",
    "timestamp", "ttl", "source_id", "perspective"
  ],
  "properties": {
    "dsig_version": {"type": "string", "enum": ["0.5"]},
    "score":        {"type": "integer", "minimum": 0, "maximum": 100},
    "label":        {"type": "string", "enum": ["EXCELLENT","GOOD","DEGRADED","CRITICAL"]},
    "color":        {"type": "string", "enum": ["GREEN","YELLOW","ORANGE","RED"]},
    "trend":        {"type": "string", "enum": ["STABLE","IMPROVING","DEGRADING","CRITICAL_FALL"]},
    "timestamp":    {"type": "string", "format": "date-time"},
    "ttl":          {"type": "integer", "minimum": 1, "maximum": 600},
    "source_id":    {"type": "string", "minLength": 1},
    "perspective":  {"type": "string", "enum": ["LOCAL","CENTRAL","EXTERNAL"]},
    "source_sig":   {"type": "string"},
    "source_pub":   {"type": "string"},
    "trust_level":  {"type": "integer", "minimum": 0, "maximum": 3},
    "baseline_cycles": {"type": "integer", "minimum": 0},
    "dimensions": {
      "type": "object",
      "additionalProperties": {
        "oneOf": [
          {"type": "number", "minimum": 0, "maximum": 100},
          {
            "type": "object",
            "required": ["score"],
            "properties": {
              "score": {"type": "number", "minimum": 0, "maximum": 100},
              "ts":    {"type": "string", "format": "date-time"},
              "ttl":   {"type": "integer", "minimum": 1},
              "flags": {"type": "array", "items": {"type": "string"}}
            }
          }
        ]
      }
    },
    "flags": {"type": "array", "items": {"type": "string"}}
  },
  "additionalProperties": false
}
```

---

*D-SIG Standard v0.5 · Public Domain CC0 · March 2026*
*Reference implementation: NetPulse v1.7+ · github.com/dsig-standard*
