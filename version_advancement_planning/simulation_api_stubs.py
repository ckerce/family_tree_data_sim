"""
Pre-Industrial Community Simulation - Core API
Version 5.0

This version (v5.0) implements a full temporal graph model to meet
the project's ML research goals (Project Context doc, Sec 7.1).

1.  RelationshipGraph is now non-destructive.
2.  'remove_relationship' is replaced by 'end_relationship'.
3.  'remove_all_relationships_for_person' is REMOVED.
4.  Graph queries ('get_outbound', 'get_inbound') now support
    an 'active_at_time' parameter for temporal filtering.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Callable
from enum import Enum
from heapq import heappush, heappop
from collections import defaultdict
import random


# ============================================================================
# LAYER 1: AGENT DATA MODELS
# ============================================================================

@dataclass
class Person:
    """Represents an individual agent in the simulation."""
    id: int
    gender: str
    birth_time: float
    death_time: Optional[float] = None
    aptitudes: Dict[str, float] = field(default_factory=dict)
    skill_hours: Dict[str, float] = field(default_factory=dict)
    
    def age(self, current_time: float) -> float:
        """Calculates the person's age in years."""
        return (current_time - self.birth_time) / 365.0
    
    def is_alive(self, current_time: float) -> bool:
        """Checks if the person is alive at the given time."""
        return self.death_time is None or self.death_time > current_time


# ============================================================================
# LAYER 2: RELATIONSHIP GRAPH (Temporal Refactor)
# ============================================================================

class RelationType(Enum):
    """Typed relationships between agents."""
    PARENT = "parent"
    PARTNER = "partner"
    APPRENTICE = "apprentice"


class RelationshipGraph:
    """
    High-performance, non-destructive temporal graph (v5.0).
    Relationships are never deleted, only timestamped with an 'end_time'.
    """
    
    def __init__(self):
        # person_a -> {person_b -> {rel_type -> metadata}}
        self.forward: Dict[int, Dict[int, Dict[RelationType, dict]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        # person_b -> {person_a -> {rel_type -> metadata}}
        self.reverse: Dict[int, Dict[int, Dict[RelationType, dict]]] = defaultdict(
            lambda: defaultdict(dict)
        )
    
    def add_relationship(
        self, 
        person_a: int, 
        person_b: int, 
        rel_type: RelationType,
        **metadata
    ):
        """
        Add directed relationship from person_a to person_b.
        'start_time' MUST be provided in metadata by the calling Event.
        """
        if 'start_time' not in metadata:
            # This is a programmatic error if this happens.
            raise ValueError(f"start_time missing for relationship {rel_type} {person_a}->{person_b}")
            
        self.forward[person_a][person_b][rel_type] = metadata
        self.reverse[person_b][person_a][rel_type] = metadata
    
    def end_relationship(
        self, 
        person_a: int, 
        person_b: int, 
        rel_type: RelationType,
        end_time: float
    ):
        """
        Ends an active relationship by adding an 'end_time' to its metadata.
        Does not delete the relationship.
        """
        try:
            self.forward[person_a][person_b][rel_type]['end_time'] = end_time
            self.reverse[person_b][person_a][rel_type]['end_time'] = end_time
        except KeyError:
            # This can happen if an event tries to end a relationship
            # that was already ended (e.g., duplicate calls).
            # It's safe to ignore.
            pass

    def _is_active(self, meta: dict, active_at_time: float) -> bool:
        """Helper to check if a relationship is active at a specific time."""
        return (meta['start_time'] <= active_at_time and
                (meta.get('end_time') is None or meta['end_time'] > active_at_time))

    def get_outbound(
        self, 
        person_id: int, 
        rel_type: Optional[RelationType] = None,
        active_at_time: Optional[float] = None
    ) -> List[Tuple[int, RelationType, dict]]:
        """
        Get relationships initiated by person.
        If 'active_at_time' is set, filters for active relationships.
        """
        matches = []
        for target, rels in self.forward.get(person_id, {}).items():
            for rtype, meta in rels.items():
                if rel_type is not None and rtype != rel_type:
                    continue
                
                if active_at_time is None:
                    # Return all (historical and active)
                    matches.append((target, rtype, meta))
                elif self._is_active(meta, active_at_time):
                    # Return only active
                    matches.append((target, rtype, meta))
        return matches
    
    def get_inbound(
        self, 
        person_id: int, 
        rel_type: Optional[RelationType] = None,
        active_at_time: Optional[float] = None
    ) -> List[Tuple[int, RelationType, dict]]:
        """
        Get relationships pointing to person.
        If 'active_at_time' is set, filters for active relationships.
        """
        matches = []
        for source, rels in self.reverse.get(person_id, {}).items():
            for rtype, meta in rels.items():
                if rel_type is not None and rtype != rel_type:
                    continue
                
                if active_at_time is None:
                    matches.append((source, rtype, meta))
                elif self._is_active(meta, active_at_time):
                    matches.append((source, rtype, meta))
        return matches
    
    def get_parents(self, person_id: int) -> List[int]:
        """Gets all (immutable) parents."""
        return [p[0] for p in self.get_inbound(person_id, RelationType.PARENT)]
    
    def get_children(self, person_id: int) -> List[int]:
        """Gets all (immutable) children."""
        return [p[0] for p in self.get_outbound(person_id, RelationType.PARENT)]


# ============================================================================
# LAYER 3: COMMUNITY (ENVIRONMENT)
# ============================================================================

# --- Data models are unchanged from v4.0 ---
@dataclass
class ProductionCapacity:
    profession: str
    good_produced: str
    base_units_per_year: float
    current_practitioners: int = 0
    avg_skill_multiplier: float = 1.0
    def annual_output(self) -> float:
        return (self.base_units_per_year * self.current_practitioners * self.avg_skill_multiplier)

@dataclass
class ConsumptionNeed:
    good: str
    units_per_capita_year: float
    current_population: int = 0
    def annual_demand(self) -> float:
        return self.units_per_capita_year * self.current_population

@dataclass
class ProfessionData:
    skill_name: str
    good_produced: str
    max_apprentices_per_master: int = 2
    apprenticeship_duration_years: int = 7
    building_required: Optional[str] = None
    base_units_per_year: float = 100.0

@dataclass
class Building:
    id: int
    type: str
    owner_id: Optional[int]
    built_time: float
    capacity: int = 1


class Community:
    """Aggregate community state and economy."""
    
    def __init__(self):
        self.profession_data: Dict[str, ProfessionData] = {}
        self.production: Dict[str, ProductionCapacity] = {}
        self.consumption: Dict[str, ConsumptionNeed] = {}
        self.market_gaps: Dict[str, float] = {}
        self.buildings: List[Building] = []
        
    def load_config(self, config: dict):
        """Populate economy rules from a configuration dictionary."""
        for prof_name, data in config.get('professions', {}).items():
            self.profession_data[prof_name] = ProfessionData(**data)
        
        for good, units in config.get('consumption', {}).items():
            self.consumption[good] = ConsumptionNeed(good=good, units_per_capita_year=units)
        
        for prof_name, prof_data in self.profession_data.items():
            good = prof_data.good_produced
            if good not in self.production:
                self.production[good] = ProductionCapacity(
                    profession=prof_name,
                    good_produced=good,
                    base_units_per_year=prof_data.base_units_per_year
                )
                
    def market_gap(self, good: str) -> float:
        """Calculate demand/supply ratio. >1 means shortage."""
        supply = (self.production[good].annual_output() 
                  if good in self.production else 0)
        demand = (self.consumption[good].annual_demand() 
                  if good in self.consumption else 0)
        
        if demand == 0: return 0.0
        if supply == 0: return float('inf')
        return demand / supply


# ============================================================================
# LAYER 4: EVENT SYSTEM
# ============================================================================

# Global counter for deterministic event tie-breaking
_event_counter = 0

class Event:
    """Base class for all simulation events."""
    def __init__(self, time: float):
        global _event_counter
        self.time = time
        self.priority = _event_counter # Deterministic tie-breaker
        _event_counter += 1
    
    def execute(self, sim: 'Simulation'):
        """Executes the event logic on the simulation state."""
        raise NotImplementedError
    
    def __lt__(self, other):
        """Sorts by time, then by insertion priority."""
        if self.time == other.time:
            return self.priority < other.priority
        return self.time < other.time


# ============================================================================
# LAYER 5: SIMULATION CONTROLLER
# ============================================================================

class Simulation:
    """Main simulation controller."""
    
    def __init__(self, seed: int = 42):
        self.time: float = 0.0
        self.event_queue: List[Event] = []
        self.population: Dict[int, Person] = {}
        self.relationships = RelationshipGraph() # Now temporal (v5.0)
        self.community = Community()
        self.professions: Dict[int, str] = {}
        self.rng = random.Random(seed)
        self._next_person_id = 0
        self._next_building_id = 0
        
        # --- Performance Indices (Unchanged from v4.0) ---
        self.practitioners_by_profession: Dict[str, Set[int]] = defaultdict(set)
        self.buildings_by_owner: Dict[int, List[Building]] = defaultdict(list)
        self.unmarried_males: Set[int] = set()
        self.unmarried_females: Set[int] = set()
        self.married_females: Set[int] = set()
        self.alive_population_count: int = 0
        self.alive_male_count: int = 0
        self.alive_female_count: int = 0
        
        self.matchmaking_strategy: Optional[MatchmakingStrategy] = None
    
    def next_person_id(self) -> int:
        self._next_person_id += 1
        return self._next_person_id
    
    def next_building_id(self) -> int:
        self._next_building_id += 1
        return self._next_building_id
    
    def schedule(self, event: Event):
        """Add event to priority queue."""
        heappush(self.event_queue, event)
    
    def run(self, max_time: float):
        """Run simulation until max_time or event queue empty."""
        global _event_counter
        _event_counter = 0
        
        try:
            while self.event_queue and self.time < max_time:
                event = heappop(self.event_queue)
                if event.time < self.time: continue 
                self.time = event.time
                event.execute(self)
        except Exception as e:
            print(f"--- SIMULATION HALTED AT t={self.time} ---")
            print(f"Error during execution of event: {event.__class__.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

    # --- Index Maintenance Methods (Unchanged from v4.0) ---
    
    def add_person_to_indices(self, person: Person):
        """Add a new person to demographic indices."""
        self.alive_population_count += 1
        if person.gender == 'male':
            self.alive_male_count += 1
            self.unmarried_males.add(person.id)
        else:
            self.alive_female_count += 1
            self.unmarried_females.add(person.id)
            
    def remove_person_from_indices(self, person: Person):
        """Remove a person from all indices upon death."""
        person_id = person.id
        self.alive_population_count -= 1
        if person.gender == 'male':
            self.alive_male_count -= 1
            self.unmarried_males.discard(person_id)
        else:
            self.alive_female_count -= 1
            self.unmarried_females.discard(person_id)
            self.married_females.discard(person_id)
        
        if person_id in self.professions:
            prof = self.professions.pop(person_id)
            self.practitioners_by_profession[prof].discard(person_id)
            
    def set_person_married(self, person_a_id: int, person_b_id: int):
        """Update demographic indices for marriage."""
        self.unmarried_males.discard(person_a_id)
        self.unmarried_females.discard(person_b_id)
        self.married_females.add(person_b_id)

    def set_person_widowed(self, person_id: int, gender: str):
        """Update demographic indices for widowhood."""
        if gender == 'male':
            self.unmarried_males.add(person_id)
        else:
            self.unmarried_females.add(person_id)
            self.married_females.discard(person_id)

    def set_person_profession(self, person_id: int, profession: str):
        """Update profession indices."""
        if person_id in self.professions:
            old_prof = self.professions[person_id]
            self.practitioners_by_profession[old_prof].discard(person_id)
        self.professions[person_id] = profession
        self.practitioners_by_profession[profession].add(person_id)
        
    def add_building(self, building: Building):
        """Update building indices."""
        self.community.buildings.append(building)
        if building.owner_id:
            self.buildings_by_owner[building.owner_id].append(building)

    def transfer_building_owner(self, building: Building, new_owner_id: Optional[int]):
        """Update building indices for inheritance."""
        old_owner_id = building.owner_id
        if old_owner_id and old_owner_id in self.buildings_by_owner:
            self.buildings_by_owner[old_owner_id].remove(building)
            if not self.buildings_by_owner[old_owner_id]:
                del self.buildings_by_owner[old_owner_id]
        building.owner_id = new_owner_id
        if new_owner_id:
            self.buildings_by_owner[new_owner_id].append(building)

    # --- Query API (Unchanged from v4.0) ---
    
    def get_alive_population(self, current_time: Optional[float] = None) -> List[int]:
        t = current_time if current_time is not None else self.time
        return [pid for pid, p in self.population.items() if p.is_alive(t)]
    
    def get_skill_level(self, person_id: int, skill: str) -> float:
        if person_id not in self.population: return 0.0
        return self.population[person_id].skill_hours.get(skill, 0.0)
    
    def get_avg_skill(self, person_ids: List[int], skill: str) -> float:
        if not person_ids: return 0.0
        total = sum(self.get_skill_level(pid, skill) for pid in person_ids)
        return total / len(person_ids)

# ============================================================================
# EXTENSIBILITY HOOKS
# ============================================================================

class MatchmakingStrategy:
    """Interface for apprenticeship matching algorithms (REQ-NF-005)."""
    
    def match(
        self, 
        candidates: List[int],
        masters_by_profession: Dict[str, List[int]],
        slots_by_profession: Dict[str, int],
        sim: Simulation
    ) -> List[Tuple[int, int, str]]:
        raise NotImplementedError
