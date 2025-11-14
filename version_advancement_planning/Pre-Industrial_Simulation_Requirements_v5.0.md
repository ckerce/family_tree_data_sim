# **Pre-Industrial Community Simulation \- Requirements Document**

Version: 5.0  
Date: 2025-11-14  
Status: Implementation Ready

## **1\. Executive Summary**

This document specifies requirements for a discrete event simulation (DES) modeling demographic, economic, and social dynamics. This version (v5.0) implements a full temporal graph model, where relationships are never deleted, only "ended" with a timestamp. This is a critical change to support the project's primary goal of generating temporal graphs for ML research.

## **2\. Goals and Objectives**

(Unchanged)

## **3\. Functional Requirements**

### **3.1 Agent Lifecycle (MUST HAVE)**

**REQ-AL-001:** (Unchanged) System SHALL model Person agents.

**REQ-AL-002:** (Unchanged) Agents SHALL age naturally.

**REQ-AL-003:** (Unchanged) Agents SHALL die based on age, infant mortality, or resource stress.

**REQ-AL-004:** (Revised) DeathEvent execution MUST:

* Set person.death\_time.  
* Remove agent from all central registries (e.g., sim.professions).  
* Remove agent from all demographic indices (e.g., sim.unmarried\_males, sim.alive\_population\_count).  
* Schedule an InheritanceEvent (REQ-BU-004).  
* **Crucially:** Mark all active, non-immutable relationships (e.g., SPOUSE, APPRENTICE) as terminated by adding an end\_time to their metadata (REQ-RG-006).

**REQ-AL-005:** (Unchanged) All events MUST check is\_alive() upon execution.

**REQ-AL-006:** (Unchanged) System SHALL model infant mortality (e.g., 25% chance at 1 year).

### **3.2 Demographic Events (MUST HAVE)**

**REQ-DE-001:** (Unchanged) System SHALL model births (BirthEvent).

**REQ-DE-002:** (Revised) A BirthEvent SHALL:

* Assign child attributes, including a gender balanced for the population.  
* Create immutable PARENT relationships with a start\_time.  
* Assign inherited aptitudes.  
* Re-validate parent liveness and marital status at execution time.

**REQ-DE-003:** (Unchanged) ReproductionCheckEvent SHALL trigger BirthEvent generation annually.

**REQ-DE-004:** (Revised) System SHALL model marriages (MarriageEvent).

* This event SHALL create symmetric SPOUSE relationships, each with a start\_time.

**REQ-DE-005:** (Unchanged) MarriageMarketEvent SHALL trigger MarriageEvent generation annually.

**REQ-DE-006:** (Unchanged) Incest prevention SHALL block siblings, parent-child, and uncle/aunt-niece/nephew.

**REQ-DE-007:** (Unchanged) System SHALL support remarriage.

### **3.3 Relationship Graph (MUST HAVE)**

**REQ-RG-001:** (Unchanged) System SHALL maintain a directed, typed relationship graph.

**REQ-RG-002:** (Revised) System SHALL support O(degree) queries:

* get\_outbound(person, type, active\_at\_time=None)  
* get\_inbound(person, type, active\_at\_time=None)  
* get\_parents(person)  
* get\_children(person)

**REQ-RG-003:** (Unchanged) System SHALL compute derived relationships on-demand.

**REQ-RG-004:** (Unchanged) System SHALL NOT store redundant derived relationships.

**REQ-RG-005:** (New) RelationshipGraph queries (get\_outbound, get\_inbound) SHALL support an active\_at\_time parameter to filter for relationships active at a specific simulation time.

**REQ-RG-006:** (New) RelationshipGraph SHALL be non-destructive.

* Ending a relationship (e.g., via death or graduation) SHALL add an end\_time to the relationship's metadata via an end\_relationship() method.  
* Relationships SHALL NOT be deleted from the graph.

### **3.4 Skills and Professions (MUST HAVE)**

(Unchanged from v4.0)

### **3.5 Aggregate Economy (MUST HAVE)**

(Unchanged from v4.0. Includes REQ-EC-006 through REQ-EC-010 for resource stress.)

### **3.6 Buildings and Infrastructure (MUST HAVE)**

(Unchanged from v4.0. Includes REQ-BU-004 for inheritance.)

### **3.7 Profession Opportunities (MUST HAVE)**

(Unchanged from v4.0)

### **3.8 Apprenticeship Lifecycle (MUST HAVE)**

**REQ-AP-001:** (Revised) Apprenticeship SHALL be created with:

* APPRENTICE relationship (master → youth) with start\_time metadata.

**REQ-AP-002:** (Unchanged) System SHALL schedule periodic SkillTransferEvent.

**REQ-AP-003:** (Revised) GraduateApprenticeshipEvent SHALL:

* **End** the APPRENTICE relationship by adding an end\_time (REQ-RG-006).  
* Assign youth the profession.  
* Trigger building construction (REQ-BU-003).

**REQ-AP-004:** (Revised) Apprenticeship SHALL terminate early if master or apprentice dies:

* DeathEvent MUST **end** the APPRENTICE relationship by adding an end\_time.

### **3.9 Event System (MUST HAVE)**

(Unchanged from v4.0. Includes ResourceStressCheckEvent.)

### **3.10 Initialization (MUST HAVE)**

(Unchanged from v4.0. Requires seeding.)

### **3.11 Data Export (MUST HAVE)**

**REQ-EX-001:** (Revised) System SHALL export to JSON:

* Person attributes (id, gender, birth\_time, death\_time).  
* **Full temporal relationships** (source, target, type, start\_time, end\_time, other\_meta).  
* Skills and professions (with timestamps).

**REQ-EX-002:** (Removed, as it's a subset of REQ-EX-001)

### **4\. Non-Functional Requirements**

(Unchanged from v4.0)