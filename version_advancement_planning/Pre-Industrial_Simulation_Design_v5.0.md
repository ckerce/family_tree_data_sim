# **Pre-Industrial Community Simulation \- Design Document**

Version: 5.0  
Date: 2025-11-14  
Status: Implementation Ready

## **1\. System Architecture**

### **1.1 Core Components**

(Unchanged. RelationshipGraph implementation is modified, but its role is the same.)

### **1.2 Component Interaction (v5.0)**

**Key Change:** DeathEvent and GraduateApprenticeshipEvent no longer delete relationships. They call sim.relationships.end\_relationship() to add an end\_time timestamp, preserving the graph history.

Initialization:  
  initialize\_simulation()  
    → ... (Unchanged from v4.0) ...  
    → Schedule annual events (Economy, Stress, Career, Repro, Marriage)

Annual Cycle (Example Year N):  
  t \= N\*365 \+ 0.1:  
    UpdateCommunityEconomyEvent.execute()  
      → ... (Unchanged from v4.0) ...

  t \= N\*365 \+ 0.2:  
    ResourceStressCheckEvent.execute()  
      → ... (Unchanged from v4.0) ...

  ... (Other annual events unchanged) ...

Event \- DeathEvent (t \= T):  
  DeathEvent.execute()  
    → Set person.death\_time \= T  
    → Find heirs, schedule InheritanceEvent(T+0.1)  
    → Query graph for \*active\* relationships (SPOUSE, APPRENTICE)  
    → FOR rel in active\_relationships:  
        → sim.relationships.end\_relationship(..., end\_time=T)  
    → Find living partner, call sim.set\_person\_widowed()  
    → call sim.remove\_person\_from\_indices()  
      
Event \- GraduateApprenticeshipEvent (t \= T):  
  GraduateApprenticeshipEvent.execute()  
    → Check if apprentice is alive  
    → sim.relationships.end\_relationship(master, apprentice, APPRENTICE, end\_time=T)  
    → sim.set\_person\_profession(...)  
    → ... (building logic) ...

## **2\. Core Components**

### **2.1 RelationshipGraph (Revised)**

The graph is now non-destructive, meeting REQ-RG-006.

**API Design:**

class RelationshipGraph:  
    def add\_relationship(self, a, b, rel\_type, \*\*metadata):  
        \# metadata MUST include 'start\_time'  
        self.forward\[a\]\[b\]\[rel\_type\] \= metadata  
        self.reverse\[b\]\[a\]\[rel\_type\] \= metadata

    def end\_relationship(self, a, b, rel\_type, end\_time):  
        \# Adds 'end\_time' key to metadata dict.  
        \# Does NOT delete the entry.  
        try:  
            self.forward\[a\]\[b\]\[rel\_type\]\['end\_time'\] \= end\_time  
            self.reverse\[b\]\[a\]\[rel\_type\]\['end\_time'\] \= end\_time  
        except KeyError:  
            pass \# Idempotent

    def \_is\_active(self, meta, time):  
        return (meta\['start\_time'\] \<= time and  
                (meta.get('end\_time') is None or meta\['end\_time'\] \> time))

    def get\_outbound(self, pid, rel\_type=None, active\_at\_time=None):  
        \# Iterates and filters relationships.  
        \# If active\_at\_time is set, uses \_is\_active helper.  
        \# ... (implementation) ...  
          
    def get\_inbound(self, pid, rel\_type=None, active\_at\_time=None):  
        \# ... (implementation) ...

### **2.2 Simulation Indices (Revised)**

(Unchanged from v4.0. Indices alive\_male\_count, etc. are still required.)

## **3\. Event Specifications (Revised v5.0)**

### **3.1 UpdateCommunityEconomyEvent (Unchanged)**

(No change from v4.0. Logic is sound.)

### **3.2 ResourceStressCheckEvent (Unchanged)**

(No change from v4.0. Logic is sound.)

### **3.3 BirthEvent (Revised)**

**Purpose:** Create a new agent and an immutable PARENT relationship.

**Pseudocode:**

def execute(self, sim):  
    \# ... (validate parents, calculate gender bias) ...  
      
    \# 3\. Create child  
    child \= Person(...)  
    sim.population\[child.id\] \= child  
    sim.add\_person\_to\_indices(child)  
      
    \# 4\. Add PARENT relationships (immutable)  
    sim.relationships.add\_relationship(  
        self.mother\_id, child.id, RelationType.PARENT,  
        start\_time=self.time  
    )  
    sim.relationships.add\_relationship(  
        self.father\_id, child.id, RelationType.PARENT,  
        start\_time=self.time  
    )  
      
    \# ... (inherit aptitudes, schedule death events) ...

### **3.4 MarriageEvent (Revised)**

**Purpose:** Create a new *temporal* SPOUSE relationship.

**Pseudocode:**

def execute(self, sim):  
    \# ... (validate liveness) ...  
              
    \# Add symmetric, temporal partner relationships  
    sim.relationships.add\_relationship(  
        self.person\_a, self.person\_b, RelationType.SPOUSE,  
        start\_time=self.time  
    )  
    sim.relationships.add\_relationship(  
        self.person\_b, self.person\_a, RelationType.SPOUSE,  
        start\_time=self.time  
    )  
      
    sim.set\_person\_married(self.person\_a, self.person\_b)

### **3.5 DeathEvent (Revised)**

**Purpose:** Clean up state and *end* (not delete) active relationships.

**Pseudocode:**

def execute(self, sim):  
    person \= sim.population\[self.person\_id\]  
    if not person or not person.is\_alive(self.time): return  
          
    \# 1\. Set state  
    person.death\_time \= self.time  
      
    \# 2\. Find heir & schedule inheritance  
    \# ... (logic unchanged) ...  
      
    \# 3\. End active, mutable relationships (REQ-AL-004)  
      
    \# 3a. End SPOUSE relationships  
    active\_partner \= sim.relationships.get\_outbound(  
        self.person\_id, RelationType.SPOUSE, active\_at\_time=self.time  
    )  
    for partner\_id, \_, \_ in active\_partner:  
        sim.relationships.end\_relationship(self.person\_id, partner\_id, RelationType.SPOUSE, self.time)  
        sim.relationships.end\_relationship(partner\_id, self.partner\_id, RelationType.SPOUSE, self.time)  
          
        \# Set living partner to widowed  
        partner \= sim.population\[partner\_id\]  
        if partner.is\_alive(self.time):  
            sim.set\_person\_widowed(partner\_id, partner.gender)  
      
    \# 3b. End APPRENTICE relationships (as master)  
    active\_apprentices \= sim.relationships.get\_outbound(  
        self.person\_id, RelationType.APPRENTICE, active\_at\_time=self.time  
    )  
    for apprentice\_id, \_, \_ in active\_apprentices:  
        sim.relationships.end\_relationship(self.person\_id, apprentice\_id, RelationType.APPRENTICE, self.time)

    \# 3c. End APPRENTICE relationships (as apprentice)  
    active\_masters \= sim.relationships.get\_inbound(  
        self.person\_id, RelationType.APPRENTICE, active\_at\_time=self.time  
    )  
    for master\_id, \_, \_ in active\_masters:  
        sim.relationships.end\_relationship(master\_id, self.person\_id, RelationType.APPRENTICE, self.time)

    \# 4\. Remove from all performance indices  
    sim.remove\_person\_from\_indices(person)  
      
    \# Note: PARENT relationships are immutable and are not ended.

### **3.6 GraduateApprenticeshipEvent (Revised)**

**Purpose:** Complete apprenticeship, *ending* the temporal relationship.

**Pseudocode:**

def execute(self, sim):  
    apprentice \= sim.population.get(self.apprentice\_id)  
      
    if not apprentice or not apprentice.is\_alive(self.time):  
        \# Apprentice died, just end the relationship if it's somehow active  
        sim.relationships.end\_relationship(  
            self.master\_id, self.apprentice\_id, RelationType.APPRENTICE, self.time  
        )  
        return  
              
    \# 1\. End apprentice relationship  
    sim.relationships.end\_relationship(  
        self.master\_id, self.apprentice\_id, RelationType.APPRENTICE, self.time  
    )  
      
    \# 2\. Assign profession  
    sim.set\_person\_profession(self.apprentice\_id, self.profession)  
      
    \# 3\. Build workshop if needed  
    \# ... (logic unchanged) ...

### **3.7 CareerMarketEvent (Revised)**

**Purpose:** Create a new *temporal* APPRENTICE relationship.

**Pseudocode:**

def execute(self, sim):  
    \# ... (slot generation, find candidates, find masters) ...  
      
    \# 4\. Match  
    matches \= sim.matchmaking\_strategy.match(...)  
      
    \# 5\. Assign  
    for youth\_id, master\_id, profession in matches:  
        \# ...  
        prof\_data \= sim.community.profession\_data\[profession\]  
        duration \= prof\_data.apprenticeship\_duration\_years  
          
        sim.relationships.add\_relationship(  
            master\_id, youth\_id, RelationType.APPRENTICE,  
            start\_time=self.time,   
            duration\_years=duration \# Store duration in metadata  
        )  
          
        sim.schedule(GraduateApprenticeshipEvent(  
            self.time \+ duration \* 365,  
            youth\_id, master\_id, profession  
        ))  
          
        \# ... (schedule skill events) ...  
      
    \# ... (default to farmer, reschedule) ...

## **4\. v5.0 Known Limitations**

* **Micro-Macro Disconnect:** Unchanged. This remains the largest conceptual gap.  
* **Export:** (REQ-EX-001) is still not implemented. This is now the highest priority task, as the data structure is ready.
