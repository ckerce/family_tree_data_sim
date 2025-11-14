# **Pre-Industrial Community Simulation \- Requirements Document**

Version: 5.0  
Date: 2025-11-14  
Status: Implementation Ready

## **1\. Executive Summary**

This document specifies requirements for a discrete event simulation (DES) modeling demographic, economic, and social dynamics. This version (v5.0) implements a full temporal graph model, where relationships are never deleted, only "ended" with a timestamp. This is a critical change to support the project's primary goal of generating temporal graphs for ML research.

## **2\. Goals and Objectives**

* Model emergent economic behavior from aggregate supply/demand dynamics.  
* Generate realistic temporal relationship graphs for machine learning research.  
* Support parameter tuning (branching factor, depth, noise injection).  
* Enable temporal and causal analysis through attribute extension.

## **3\. Functional Requirements**

### **3.1 Agent Lifecycle (MUST HAVE)**

**REQ-AL-001:** System SHALL model Person agents with attributes:

* Unique ID, Gender, Birth/Death time  
* aptitudes: Dict\[str, float\]  
* skill\_hours: Dict\[str, float\]

**REQ-AL-002:** Agents SHALL age naturally.

**REQ-AL-003:** Agents SHALL die based on age-based mortality, infant mortality (REQ-AL-006), or resource-driven stress (REQ-EC-006).

**REQ-AL-004:** DeathEvent execution MUST:

* Set person.death\_time.  
* Remove agent from all central registries (e.g., sim.professions).  
* Remove agent from all demographic indices (e.g., sim.unmarried\_males, sim.alive\_population\_count).  
* Schedule an InheritanceEvent (REQ-BU-004).  
* **Crucially:** Mark all active, non-immutable relationships (e.g., SPOUSE, APPRENTICE) as terminated by adding an end\_time to their metadata (REQ-RG-006).

**REQ-AL-005:** All events MUST check is\_alive() upon execution.

**REQ-AL-006:** System SHALL model infant mortality (e.g., an InfantMortalityCheckEvent with a 25% probability at t \+ 1\_year).

### **3.2 Demographic Events (MUST HAVE)**

**REQ-DE-001:** System SHALL model births (BirthEvent).

**REQ-DE-002:** A BirthEvent SHALL:

* Assign child attributes, including a gender balanced for the population.  
* Create immutable PARENT relationships with a start\_time.  
* Assign inherited aptitudes (e.g., average of parents \+ gauss(0, 0.15) noise).  
* Re-validate parent liveness and marital status at execution time.

**REQ-DE-003:** ReproductionCheckEvent SHALL trigger BirthEvent generation annually based on:

* Female age (e.g., 20-50), *living* spouse, and existing children.  
* Formula, e.g., P \= 0.32 / (1.0 \+ 2.0 \* children\_count).

**REQ-DE-004:** System SHALL model marriages (MarriageEvent).

* This event SHALL create symmetric SPOUSE relationships, each with a start\_time.

**REQ-DE-005:** MarriageMarketEvent SHALL trigger MarriageEvent generation annually.

**REQ-DE-006:** Incest prevention SHALL block siblings, parent-child, and uncle/aunt-niece/nephew.

**REQ-DE-007:** System SHALL support remarriage. MarriageMarketEvent and ReproductionCheckEvent MUST check spouse.is\_alive() and allow new relationships if spouse is deceased (via set\_person\_widowed logic).

### **3.3 Relationship Graph (MUST HAVE)**

**REQ-RG-001:** System SHALL maintain a directed, typed relationship graph.

**REQ-RG-002:** System SHALL support O(degree) queries:

* get\_outbound(person, type, active\_at\_time=None)  
* get\_inbound(person, type, active\_at\_time=None)  
* get\_parents(person)  
* get\_children(person)

**REQ-RG-003:** System SHALL compute derived relationships on-demand.

**REQ-RG-004:** System SHALL NOT store redundant derived relationships.

**REQ-RG-005:** RelationshipGraph queries (get\_outbound, get\_inbound) SHALL support an active\_at\_time parameter to filter for relationships active at a specific simulation time.

**REQ-RG-006:** RelationshipGraph SHALL be non-destructive.

* Ending a relationship (e.g., via death or graduation) SHALL add an end\_time to the relationship's metadata via an end\_relationship() method.  
* Relationships SHALL NOT be deleted from the graph.

### **3.4 Skills and Professions (MUST HAVE)**

**REQ-SP-001:** Person SHALL have aptitudes and skill\_hours.

**REQ-SP-002:** System SHALL track profession assignment per person.

**REQ-SP-003:** Professions SHALL be defined by configurable data.

**REQ-SP-004:** Skill development SHALL occur via SkillTransferEvent.

**REQ-SP-005:** Learning rate SHALL be:

* effective\_hours \= base\_hours \* aptitude \* master\_skill\_bonus  
* master\_skill\_bonus SHALL be, e.g., 1.0 \+ min(1.0, master\_hours / 10000\).

### **3.5 Aggregate Economy (MUST HAVE)**

**REQ-EC-001:** System SHALL model goods at an aggregate level.

**REQ-EC-002:** ProductionCapacity SHALL track current\_practitioners, avg\_skill\_multiplier.

**REQ-EC-003:** ConsumptionNeed SHALL track current\_population.

**REQ-EC-004:** System SHALL calculate market\_gap \= annual\_demand / annual\_output.

**REQ-EC-005:** UpdateCommunityEconomyEvent SHALL update economy annually.

* avg\_skill\_multiplier formula SHALL be, e.g., 1.0 \+ min(1.0, avg\_hours / 20000.0).

**REQ-EC-006:** System SHALL model population pressure from resource shortages (representing starvation, disease, and emigration).

**REQ-EC-007:** A periodic ResourceStressCheckEvent SHALL execute annually.

**REQ-EC-008:** This event SHALL calculate the shortfall for critical goods (e.g., 'food').

* Shortfall % SHALL be calculated as 1.0 \- (1.0 / market\_gap).

**REQ-EC-009:** If a shortfall exists, the event SHALL schedule additional DeathEvents.

* The number of exits SHALL be proportional to the shortfall, e.g., N\_exits \= N\_population \* shortfall\_pct \* K, where K is a conversion factor.

**REQ-EC-010:** This population exit mechanism SHALL target vulnerable agents (e.g., young, old, unemployed) with higher probability.

### **3.6 Buildings and Infrastructure (MUST HAVE)**

**REQ-BU-001:** System SHALL model Building (type, owner\_id, built\_time).

**REQ-BU-002:** UpdateCommunityEconomyEvent MUST enforce building requirements for production.

**REQ-BU-003:** GraduateApprenticeshipEvent SHALL construct buildings if required.

**REQ-BU-004:** System SHALL model building inheritance. A DeathEvent SHALL schedule an InheritanceEvent to transfer Building.owner\_id to an heir (e.g., eldest living child). If no heir, building owner is set to None.

### **3.7 Profession Opportunities (MUST HAVE)**

**REQ-PO-001:** CareerMarketEvent SHALL generate slots.

* Logic must gracefully handle market\_gap \= inf (e.g., treat as max probability).  
* Formula, e.g., P \= min(1.0, gap \- 1.3) for gap \> 1.3.

**REQ-PO-002:** Opportunity generation SHALL be an annual batch process.

**REQ-PO-003:** System SHALL limit apprentice slots by master capacity.

**REQ-PO-004:** System SHALL match youth to masters using a pluggable strategy.

**REQ-PO-005:** Unmatched, eligible youth SHALL default to 'farmer' (or a configurable default).

### **3.8 Apprenticeship Lifecycle (MUST HAVE)**

**REQ-AP-001:** Apprenticeship SHALL be created with:

* APPRENTICE relationship (master → youth) with start\_time metadata.

**REQ-AP-002:** System SHALL schedule periodic SkillTransferEvent.

**REQ-AP-003:** GraduateApprenticeshipEvent SHALL:

* **End** the APPRENTICE relationship by adding an end\_time (REQ-RG-006).  
* Assign youth the profession.  
* Trigger building construction (REQ-BU-003).

**REQ-AP-004:** Apprenticeship SHALL terminate early if master or apprentice dies:

* DeathEvent MUST **end** the APPRENTICE relationship by adding an end\_time.

### **3.9 Event System (MUST HAVE)**

**REQ-EV-001:** System SHALL use a DES priority queue.

**REQ-EV-002:** Event types SHALL include:

* BirthEvent, DeathEvent, MarriageEvent  
* ReproductionCheckEvent, MarriageMarketEvent (Annual)  
* UpdateCommunityEconomyEvent, CareerMarketEvent (Annual)  
* ResourceStressCheckEvent (Annual)  
* SkillTransferEvent (Periodic)  
* GraduateApprenticeshipEvent  
* InheritanceEvent  
* InfantMortalityCheckEvent

**REQ-EV-003:** Event execution SHALL be atomic.

**REQ-EV-004:** Events SHALL be scheduled with sub-day precision to enforce ordering (e.g., Economy @ t+0.1, Stress @ t+0.2, Career @ t+0.5).

### **3.10 Initialization (MUST HAVE)**

**REQ-IN-001:** Simulation SHALL initialize with:

* Small population (e.g., 8 people, 2 married couples).  
* Ages 20-30.  
* **Crucially:** Initial population MUST be seeded with professions, skills, and buildings to bootstrap the economy.

**REQ-IN-002:** Simulation SHALL load economy config from external source.

**REQ-IN-003:** Simulation SHALL run until max\_time or extinction.

### **3.11 Data Export (MUST HAVE)**

**REQ-EX-001:** System SHALL export to JSON:

* Person attributes (id, gender, birth\_time, death\_time).  
* **Full temporal relationships** (source, target, type, start\_time, end\_time, other\_meta).  
* Skills and professions (with timestamps).

## **4\. Non-Functional Requirements**

### **4.1 Performance**

**REQ-NF-001:** Simulation SHALL handle 1,000 agents with \<10s execution time for 1,000 simulation years.

**REQ-NF-002:** Relationship queries SHALL be O(degree).

**REQ-NF-003:** Annual demographic and economic events SHALL NOT use O(N) population scans. They SHALL use specialized indices (e.g., practitioners\_by\_profession, married\_females, alive\_population\_count, alive\_male\_count, alive\_female\_count) for O(1) or O(index\_size) lookups.

### **4.2 Extensibility**

**REQ-NF-004:** Architecture SHALL support adding:

* New relationship types without modifying core graph.  
* New event types without modifying scheduler.  
* New professions via external configuration.  
* New goods via external configuration.

**REQ-NF-005:** Matchmaking strategy SHALL be pluggable.

### **4.3 Determinism**

**REQ-NF-006:** Simulation SHALL produce identical results with same seed.

**REQ-NF-007:** Event timestamps SHALL be unique. A secondary, deterministic tie-breaker (e.g., an incrementing counter) MUST be used.