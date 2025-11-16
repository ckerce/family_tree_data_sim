# Pre-Industrial Community Simulation - Project Context

**Version:** 1.0  
**Date:** 2025-11-14  
**Status:** Reference Document

---

## 1. Primary Purpose

This simulation is a **data generation platform** for machine learning research. It produces labeled temporal relational graphs suitable for investigating neural inductive logic programming (ILP), graph neural networks (GNNs), and temporal reasoning methods.

**The simulation is NOT:**
- A predictive model of specific historical populations
- An economic simulator with individual agent transactions
- A runtime platform for integrated ML agents
- Optimized for empirical calibration to historical data

**The simulation IS:**
- A discrete event system modeling pre-industrial community dynamics
- A generator of rich relational structures with temporal causality
- A research platform for exploring emergent social patterns
- A parameterizable system for investigating how simple rules produce complex networks

---

## 2. Output Requirements

### 2.1 Temporal Relational Graph Format

The simulation must export graphs with:

**Nodes:** Person agents with attributes
- Unique ID
- Gender
- Birth/death timestamps
- Aptitudes (skill → float)
- Skill accumulation over time (skill → hours)
- Profession assignments with timestamps

**Edges:** Typed relationships with temporal bounds
- PARENT (person_a → person_b, start_time, immutable)
- PARTNER (bidirectional, start_time, end_time on death/widowhood)
- APPRENTICE (master → apprentice, start_time, end_time on graduation/death)
- Future types: SIBLING, TRADE_PARTNER, PATRON, etc.

**Events:** Discrete occurrences with causal chains
- Birth, Death, Marriage
- Apprenticeship start/graduation
- Profession assignment
- Skill transfer milestones

### 2.2 Learnable Patterns

The graph should enable ILP/GNN methods to discover patterns like:

**Kinship-based patterns:**
- "Siblings have correlated aptitudes"
- "Children of skilled parents become apprentices earlier"
- "Uncle-nephew relationships predict apprenticeship matches"

**Skill-based patterns:**
- "Apprentices to masters with high skill_hours develop faster"
- "Profession switches correlate with market conditions"
- "Skill accumulation rate predicts graduation success"

**Temporal patterns:**
- "Partnership at age X predicts Y children"
- "Early apprenticeships lead to earlier mastery"
- "Death clustering indicates resource stress events"

**Critical requirement:** Patterns must be non-trivial. Purely deterministic rules (e.g., "all 16-year-olds without profession become farmers") provide nothing to learn.

---

## 3. Scope Boundaries

### 3.1 Core Domains (In Scope)

**Demographics:**
- Birth, aging, death (natural, infant mortality, resource-driven)
- Partnership, reproduction, widowhood
- Kinship networks (parent-child, siblings, extended family)
- Gender ratio dynamics

**Skills and Professions:**
- Aptitude inheritance with noise
- Skill accumulation via apprenticeship
- Master-apprentice relationships
- Profession assignment based on market gaps
- Career transitions

**Social Structure:**
- Relationship networks (family, apprenticeship, future: patronage)
- Building ownership and inheritance
- Social roles (master craftsman, apprentice, farmer)

### 3.2 Economic Systems (Supporting Role Only)

**Aggregate economy exists solely as closure mechanism:**
- Determines when profession slots open (market gaps)
- Creates population pressure via resource shortages
- Drives building construction timing

**Explicitly OUT of scope:**
- Individual inventory or wealth
- Person-to-person transactions
- Price discovery mechanisms
- Individual economic decision-making
- Trade networks or markets

**Rationale:** Economic factors are "environmental physics" that make relational event timing realistic. They are NOT the subject of ML investigation.

### 3.3 Explicitly Out of Scope

- Real-time ML integration or agent learning
- Historical accuracy or empirical validation
- Individual resource consumption/production
- Detailed simulation of specific cultures/regions
- User interface or visualization beyond data export

---

## 4. Architectural Success Criteria

### 4.1 Functional Requirements

1. **Export completeness:** Can serialize entire temporal graph with relationship history
2. **Temporal fidelity:** All events have precise timestamps; causal ordering preserved
3. **Relationship persistence:** Dead agents' relationships retained with end_time metadata
4. **Pattern richness:** Non-deterministic elements ensure learnable patterns exist
5. **Extensibility:** Can add new relationship types without architectural changes

### 4.2 Performance Requirements

- Handle 1000+ agents over 1000 simulated years
- Event processing efficiency (O(degree) relationship queries, indexed demographic lookups)
- Deterministic results for reproducibility

### 4.3 Data Quality Requirements

- Emergent population dynamics (growth, crashes, recovery)
- Realistic profession distributions driven by demand
- Multi-generational kinship networks
- Skill development shows variance and correlation with mentorship quality

---

## 5. Design Philosophy

### 5.1 Emergence Over Calibration

Simple, ungrounded dynamics are acceptable. The goal is observing what emerges from parameter combinations, not matching historical data.

**Examples:**
- K_CONVERSION_FACTOR = 0.2 for resource stress is a starting point, not a fitted value
- Gender correction strength of 0.2 is exploratory
- Linear shortfall calculations are fine if they produce interesting dynamics

Parameter exploration reveals which mechanisms generate rich relational patterns, not which values match reality.

### 5.2 Individual Relationships Matter; Individual Economics Don't

Agents have:
- Rich relationship networks (explicit edges in graph)
- Skill development trajectories (node features over time)
- Life event histories (birth, marriage, career, death)

Agents do NOT have:
- Personal wealth or inventory
- Transaction histories
- Individual resource consumption
- Economic decision-making autonomy

This asymmetry is intentional: relationships are the research subject; economics are environmental constraints.

### 5.3 Causality Must Be Observable

For temporal reasoning research, causal chains must be explicit in the output:
- Marriage (t₁) → BirthEvent scheduled (t₂) → Child node created (t₃)
- Shortage detected (t₁) → ResourceStressCheckEvent (t₂) → DeathEvents scheduled (t₃)
- Skill threshold reached (t₁) → GraduationEvent (t₂) → Profession assigned (t₃)

Events should reference triggering conditions where relevant (e.g., "CareerMarketEvent created apprenticeship because food_gap = 2.3").

### 5.4 Simple Mechanisms Over Complex Subsystems

Prefer:
- Aggregate economic calculations over individual transaction processing
- Annual batch events over continuous monitoring
- Direct probability formulas over complex state machines

Complex emergent behavior should arise from interactions between simple mechanisms, not from complicated individual components.

---

## 6. Known Architectural Constraints

### 6.1 Aggregate Economy

**Constraint:** Community-level production/consumption only; no individual economics.

**Implications:**
- Cannot model wealth inequality or individual trading behavior
- Economic causality hidden inside aggregate calculations
- No economic edges in the relational graph

**Justification:** Economics serve only to time profession assignments and create population pressure. Individual economic agency adds complexity without supporting research goals.

**Reversibility:** High cost if individual economics later needed for ML research. Would require adding inventory, transactions, refactoring all economic events.

### 6.2 Event-Driven Architecture

**Constraint:** Discrete event simulation with priority queue; no time-stepped updates.

**Implications:**
- All state changes occur via Event.execute()
- Temporal precision at event granularity
- Causality tracking natural but requires event references

**Justification:** Clean temporal semantics; events map directly to graph edges/labels.

**Reversibility:** Low cost; could add time-stepped updates alongside events if needed.

### 6.3 Manual Index Maintenance

**Constraint:** Performance indices (practitioners_by_profession, married_females, etc.) updated explicitly by events.

**Implications:**
- Event classes coupled to Simulation indices
- Adding new queries requires new indices and update logic
- Maintenance burden grows with index count

**Justification:** Avoids O(N) population scans in annual events; keeps events responsive.

**Reversibility:** Moderate cost; could refactor to event sourcing or query objects.

---

## 7. Implementation Priorities

### Essential for Research Goal Fulfillment

**Export system:** Cannot generate ML datasets without serialization capability. Must include:
- All person attributes with temporal bounds (birth_time, death_time)
- Complete relationship history with start_time and end_time
- Event causality metadata where relevant to temporal reasoning

**Temporal graph integrity:** Relationships must persist beyond agent death to support temporal pattern learning. Non-destructive graph operations required.

**Pattern richness validation:** Mechanisms must produce non-deterministic, learnable patterns. Purely deterministic rules (e.g., "all unemployed 16-year-olds become farmers") provide nothing for ILP/GNN methods to discover.

### Architectural Readiness

The system maintains extensibility without premature implementation:
- New RelationType values via enum extension (e.g., SIBLING, PATRON, RIVAL)
- Additional relationship metadata via dictionary expansion
- Alternative event strategies via strategy pattern (see MatchmakingStrategy)
- Configurable event schedules via parameter injection

Add features when research needs justify them, not speculatively.

---

## 8. Success Metrics

The simulation succeeds when:

1. **Exports complete temporal graphs** with 100+ nodes, 500+ edges, spanning 200+ years
2. **Generates emergent patterns** observable in population dynamics and profession distributions
3. **Enables ML research** by providing labeled data where non-trivial relational patterns exist
4. **Supports parameter exploration** across multiple runs with different configurations
5. **Maintains extensibility** such that new relationship types require minimal changes

The simulation does NOT need to:
- Match historical demographic data
- Produce economically "realistic" prices or wealth distributions
- Run in real-time or support interactive queries
- Scale beyond 10,000 agents or 2,000 years

---

## 9. Relationship to Requirements/Design Documents

**Requirements Document (v4.0):** Specifies functional requirements (REQ-AL-*, REQ-DE-*, etc.). All requirements remain valid but should be interpreted through this context document.

**Design Document (v4.0):** Specifies implementation details. Architectural decisions (aggregate economy, event system, indices) align with goals stated here.

**API Document (v4.0):** Defines data structures and interfaces. Agent Layer (Person, RelationshipGraph) is the research subject; Environment Layer (Community) is supporting infrastructure.

**When conflicts arise:** This context document takes precedence for architectural decisions. Requirements/design docs govern implementation details within established architecture.

---

## 10. Open Questions

1. **Export format specification:** What graph serialization format best supports ILP/GNN tools?
2. **Relationship metadata schema:** What additional edge attributes would enhance learnability?
3. **Event causality encoding:** How to represent "Event A triggered Event B" in exported data?
4. **Minimum population scale:** What graph size is needed for meaningful ILP research?
5. **Parameter sensitivity:** Which mechanisms most strongly affect pattern richness?

These should be resolved through prototyping and consultation with ML research requirements.
