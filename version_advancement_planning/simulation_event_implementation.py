"""
Event Implementations for Pre-Industrial Community Simulation
Version 5.0

Implements all event classes specified in sim_design_v5.md.

This version (v5.0) implements the temporal graph refactor:
1.  Imports from 'sim_api_v5'.
2.  DeathEvent now calls 'end_relationship' instead of 'remove_all'.
3.  GraduateApprenticeshipEvent calls 'end_relationship'.
4.  All 'add_relationship' calls include a 'start_time'.
"""

from sim_api_v5 import (
    Simulation, Event, Person, Building, RelationType, 
    MatchmakingStrategy, ProfessionData
)
from typing import List, Tuple, Dict, Optional
from collections import defaultdict
import random
import json

# ============================================================================
# DEMOGRAPHIC EVENTS
# ============================================================================

class BirthEvent(Event):
    """Birth of a child to a married couple."""
    
    def __init__(self, time: float, mother_id: int, father_id: int):
        super().__init__(time)
        self.mother_id = mother_id
        self.father_id = father_id
    
    def execute(self, sim: 'Simulation'):
        mother = sim.population.get(self.mother_id)
        father = sim.population.get(self.father_id)
        
        if not mother or not father or \
           not mother.is_alive(self.time) or not father.is_alive(self.time):
            return
        
        spouses = sim.relationships.get_outbound(self.mother_id, RelationType.SPOUSE, active_at_time=self.time)
        if not spouses or spouses[0][0] != self.father_id:
            return
        
        # Calculate gender bias
        if sim.alive_population_count > 0:
            male_ratio = sim.alive_male_count / sim.alive_population_count
        else:
            male_ratio = 0.5
        prob_male = 0.5 + (0.5 - male_ratio) * 0.2
        gender = 'male' if sim.rng.random() < prob_male else 'female'
        
        # Create child
        child = Person(
            id=sim.next_person_id(),
            gender=gender,
            birth_time=self.time
        )
        sim.population[child.id] = child
        sim.add_person_to_indices(child)
        
        # Add immutable PARENT relationships
        sim.relationships.add_relationship(
            self.mother_id, child.id, RelationType.PARENT, start_time=self.time
        )
        sim.relationships.add_relationship(
            self.father_id, child.id, RelationType.PARENT, start_time=self.time
        )
        
        # Initialize aptitudes
        for skill in sim.community.profession_data.keys():
            skill_name = sim.community.profession_data[skill].skill_name
            mother_apt = mother.aptitudes.get(skill_name, 1.0)
            father_apt = father.aptitudes.get(skill_name, 1.0)
            mean = (mother_apt + father_apt) / 2
            noise = sim.rng.gauss(0, 0.15)
            child.aptitudes[skill_name] = max(0.5, min(1.5, mean + noise))
        
        sim.schedule(InfantMortalityCheckEvent(self.time + 365, child.id, 0.25))
        death_age = sim.rng.gauss(65, 10)
        sim.schedule(DeathEvent(self.time + death_age * 365, child.id))


class InfantMortalityCheckEvent(Event):
    """Stochastic check for infant death (REQ-AL-006)."""
    
    def __init__(self, time: float, child_id: int, probability: float):
        super().__init__(time)
        self.child_id = child_id
        self.probability = probability
        
    def execute(self, sim: 'Simulation'):
        child = sim.population.get(self.child_id)
        if not child or not child.is_alive(self.time):
            return
        if sim.rng.random() < self.probability:
            sim.schedule(DeathEvent(self.time, self.child_id))


class DeathEvent(Event):
    """
    Comprehensive agent state cleanup (REQ-AL-004).
    v5.0: Ends relationships instead of deleting them.
    """
    
    def __init__(self, time: float, person_id: int):
        super().__init__(time)
        self.person_id = person_id
    
    def execute(self, sim: 'Simulation'):
        person = sim.population.get(self.person_id)
        if not person or not person.is_alive(self.time):
            return
        
        # 1. Set state
        person.death_time = self.time
        
        # 2. Find heir & schedule inheritance (REQ-BU-004)
        heir_id = None
        children = sim.relationships.get_outbound(self.person_id, RelationType.PARENT) # PARENT rels are immutable
        if children:
            children_by_age = sorted(
                [(sim.population[cid], cid) for cid, _, _ in children if sim.population[cid].is_alive(self.time)],
                key=lambda p: p[0].birth_time
            )
            if children_by_age:
                heir_id = children_by_age[0][1]
                    
        sim.schedule(InheritanceEvent(self.time + 0.1, self.person_id, heir_id))

        # 3. End active, mutable relationships (REQ-AL-004)
        
        # 3a. End SPOUSE relationships
        active_spouses = sim.relationships.get_outbound(
            self.person_id, RelationType.SPOUSE, active_at_time=self.time
        )
        for spouse_id, _, _ in active_spouses:
            sim.relationships.end_relationship(self.person_id, spouse_id, RelationType.SPOUSE, self.time)
            sim.relationships.end_relationship(spouse_id, self.person_id, RelationType.SPOUSE, self.time)
            
            # Set living spouse to widowed
            spouse = sim.population[spouse_id]
            if spouse.is_alive(self.time):
                sim.set_person_widowed(spouse_id, spouse.gender)
        
        # 3b. End APPRENTICE relationships (as master)
        active_apprentices = sim.relationships.get_outbound(
            self.person_id, RelationType.APPRENTICE, active_at_time=self.time
        )
        for apprentice_id, _, _ in active_apprentices:
            sim.relationships.end_relationship(self.person_id, apprentice_id, RelationType.APPRENTICE, self.time)

        # 3c. End APPRENTICE relationships (as apprentice)
        active_masters = sim.relationships.get_inbound(
            self.person_id, RelationType.APPRENTICE, active_at_time=self.time
        )
        for master_id, _, _ in active_masters:
            sim.relationships.end_relationship(master_id, self.person_id, RelationType.APPRENTICE, self.time)
        
        # 4. Remove from all performance indices
        sim.remove_person_from_indices(person)
        
        # Note: PARENT relationships are immutable and are not ended.


class InheritanceEvent(Event):
    """Transfer assets from deceased to heir (REQ-BU-004)."""
    
    def __init__(self, time: float, deceased_id: int, heir_id: Optional[int]):
        super().__init__(time)
        self.deceased_id = deceased_id
        self.heir_id = heir_id
        
    def execute(self, sim: 'Simulation'):
        buildings = sim.buildings_by_owner.get(self.deceased_id, []).copy()
        if not buildings:
            return
            
        heir = sim.population.get(self.heir_id) if self.heir_id else None
        
        for building in buildings:
            if heir and heir.is_alive(self.time):
                sim.transfer_building_owner(building, heir.id)
            else:
                sim.transfer_building_owner(building, None) # Orphan


class MarriageEvent(Event):
    """Create temporal spouse relationship and update indices."""
    
    def __init__(self, time: float, person_a: int, person_b: int):
        super().__init__(time)
        self.person_a = person_a # Male
        self.person_b = person_b # Female
    
    def execute(self, sim: 'Simulation'):
        person_a = sim.population.get(self.person_a)
        person_b = sim.population.get(self.person_b)
        
        if not person_a or not person_b or \
           not person_a.is_alive(self.time) or not person_b.is_alive(self.time):
            return
            
        sim.relationships.add_relationship(
            self.person_a, self.person_b, RelationType.SPOUSE, start_time=self.time
        )
        sim.relationships.add_relationship(
            self.person_b, self.person_a, RelationType.SPOUSE, start_time=self.time
        )
        
        sim.set_person_married(self.person_a, self.person_b)

# ============================================================================
# ANNUAL DEMOGRAPHIC EVENTS (Triggers)
# ============================================================================

class ReproductionCheckEvent(Event):
    """Annual check to schedule new births (REQ-DE-003)."""
    
    def __init__(self, time: float):
        super().__init__(time)
        
    def execute(self, sim: 'Simulation'):
        for person_id in list(sim.married_females):
            person = sim.population[person_id]
            
            if not person.is_alive(self.time):
                continue
            if not (20 <= person.age(self.time) <= 50):
                continue

            spouses = sim.relationships.get_outbound(person.id, RelationType.SPOUSE, active_at_time=self.time)
            if not spouses:
                continue
            
            spouse_id = spouses[0][0]
            if not sim.population[spouse_id].is_alive(self.time):
                continue
                
            children_count = len(sim.relationships.get_outbound(person.id, RelationType.PARENT))
            max_children = 8
            base_prob = 0.32
            
            if children_count >= max_children:
                continue
                
            birth_prob = base_prob / (1.0 + 2.0 * children_count)
            
            if sim.rng.random() < birth_prob:
                sim.schedule(BirthEvent(self.time, person.id, spouse_id))
        
        sim.schedule(ReproductionCheckEvent(self.time + 365))


class MarriageMarketEvent(Event):
    """Annual check to schedule new marriages (REQ-DE-005)."""
    
    def __init__(self, time: float):
        super().__init__(time)
        
    def execute(self, sim: 'Simulation'):
        min_age = 20
        
        males = [pid for pid in sim.unmarried_males 
                 if sim.population[pid].is_alive(self.time) and 
                 sim.population[pid].age(self.time) >= min_age]
        females = [pid for pid in sim.unmarried_females
                   if sim.population[pid].is_alive(self.time) and
                   sim.population[pid].age(self.time) >= min_age]
        
        sim.rng.shuffle(males)
        sim.rng.shuffle(females)
        
        used_females = set()
        for male_id in males:
            for female_id in females:
                if female_id in used_females: continue
                
                if self._is_related(sim, male_id, female_id):
                    continue
                    
                sim.schedule(MarriageEvent(self.time, male_id, female_id))
                used_females.add(female_id)
                break
                
        sim.schedule(MarriageMarketEvent(self.time + 365))

    def _is_related(self, sim: 'Simulation', male_id: int, female_id: int) -> bool:
        """Broadened incest check (REQ-DE-006)."""
        male_parents = set(sim.relationships.get_parents(male_id))
        female_parents = set(sim.relationships.get_parents(female_id))
        
        if male_parents and male_parents.intersection(female_parents):
            return True
        if male_id in female_parents or female_id in male_parents:
            return True
            
        male_grandparents = set(gp for p in male_parents for gp in sim.relationships.get_parents(p))
        female_grandparents = set(gp for p in female_parents for gp in sim.relationships.get_parents(p))
        
        if (male_parents and male_parents.intersection(female_grandparents)) or \
           (female_parents and female_parents.intersection(male_grandparents)):
            return True
            
        return False

# ============================================================================
# ECONOMIC EVENTS
# ============================================================================

class UpdateCommunityEconomyEvent(Event):
    """Annual economic update (REQ-EC-005)."""
    
    def __init__(self, time: float):
        super().__init__(time)
    
    def execute(self, sim: 'Simulation'):
        alive_pop_count = sim.alive_population_count
        
        for good, need in sim.community.consumption.items():
            need.current_population = alive_pop_count
        
        for profession, capacity in sim.community.production.items():
            prof_data = sim.community.profession_data[profession]
            skill_name = prof_data.skill_name
            
            potential_practitioners = sim.practitioners_by_profession.get(profession, set())
            qualified_practitioners = []
            
            for pid in potential_practitioners:
                person = sim.population[pid]
                if not person.is_alive(self.time): continue
                
                if prof_data.building_required:
                    buildings = sim.buildings_by_owner.get(pid, [])
                    if any(b.type == prof_data.building_required for b in buildings):
                        qualified_practitioners.append(pid)
                else:
                    qualified_practitioners.append(pid)
                    
            capacity.current_practitioners = len(qualified_practitioners)
            
            if qualified_practitioners:
                avg_hours = sim.get_avg_skill(qualified_practitioners, skill_name)
                capacity.avg_skill_multiplier = 1.0 + min(1.0, avg_hours / 20000.0)
            else:
                capacity.avg_skill_multiplier = 1.0
        
        for good in sim.community.consumption.keys():
            sim.community.market_gaps[good] = sim.community.market_gap(good)
        
        sim.schedule(UpdateCommunityEconomyEvent(self.time + 365))


class ResourceStressCheckEvent(Event):
    """Annual check for resource-driven population pressure (REQ-EC-007)."""
    
    def __init__(self, time: float, critical_goods: List[str] = ['food']):
        super().__init__(time)
        self.critical_goods = critical_goods
    
    def execute(self, sim: 'Simulation'):
        max_shortfall_pct = 0.0
        for good in self.critical_goods:
            gap = sim.community.market_gaps.get(good, 0.0)
            if gap > 1.0:
                shortfall_pct = 1.0 - (1.0 / gap) if gap != float('inf') else 1.0
                max_shortfall_pct = max(max_shortfall_pct, shortfall_pct)

        if max_shortfall_pct == 0.0:
            sim.schedule(ResourceStressCheckEvent(self.time + 365, self.critical_goods))
            return
            
        K_CONVERSION_FACTOR = 0.2
        n_to_remove = int(sim.alive_population_count * max_shortfall_pct * K_CONVERSION_FACTOR)
        
        if n_to_remove > 0:
            candidates = [pid for pid, p in sim.population.items() if p.is_alive(self.time)]
            victims = self._select_victims(sim, candidates, n_to_remove)
            
            for person_id in victims:
                sim.schedule(DeathEvent(self.time + sim.rng.random() * 0.1, person_id))
        
        sim.schedule(ResourceStressCheckEvent(self.time + 365, self.critical_goods))

    def _select_victims(self, sim: Simulation, candidates: List[int], n: int) -> List[int]:
        """Selects most vulnerable agents (REQ-EC-010)."""
        if n >= len(candidates):
            return candidates
            
        weighted = []
        for pid in candidates:
            person = sim.population[pid]
            age = person.age(self.time)
            weight = 1.0
            if age < 5 or age > 60: weight *= 3.0
            if pid not in sim.professions: weight *= 2.0
            weighted.append((weight * sim.rng.random(), pid))
            
        weighted.sort(reverse=True, key=lambda x: x[0])
        return [pid for _, pid in weighted[:n]]


class CareerMarketEvent(Event):
    """Annual career market (REQ-PO-001)."""
    
    def __init__(self, time: float):
        super().__init__(time)
        
    def execute(self, sim: 'Simulation'):
        if not sim.matchmaking_strategy:
            sim.schedule(CareerMarketEvent(self.time + 365))
            return
            
        slots_by_profession = defaultdict(int)
        MAX_GAP_PROB = 1.0
        THRESHOLD = 1.3
        
        for good, gap in sim.community.market_gaps.items():
            profession = self._find_profession_for_good(good, sim)
            if profession is None: continue
            
            if gap == float('inf'):
                probability = MAX_GAP_PROB
            elif gap > THRESHOLD:
                probability = min(MAX_GAP_PROB, gap - THRESHOLD)
            else:
                probability = 0.0
                
            if sim.rng.random() < probability:
                slots_by_profession[profession] += 1
        
        eligible_youth = []
        for pid, person in sim.population.items():
            if person.is_alive(self.time) \
               and 16 <= person.age(self.time) <= 20 \
               and pid not in sim.professions:
                eligible_youth.append(pid)
        
        available_masters = defaultdict(list)
        for prof_name in slots_by_profession:
            prof_data = sim.community.profession_data[prof_name]
            for master_id in sim.practitioners_by_profession.get(prof_name, set()):
                if not sim.population[master_id].is_alive(self.time): continue
                
                current_apprentices = len(sim.relationships.get_outbound(
                    master_id, RelationType.APPRENTICE, active_at_time=self.time
                ))
                if current_apprentices < prof_data.max_apprentices_per_master:
                    available_masters[prof_name].append(master_id)
        
        matches = sim.matchmaking_strategy.match(
            eligible_youth, available_masters, slots_by_profession, sim
        )
        
        matched_youth = set()
        for youth_id, master_id, profession in matches:
            matched_youth.add(youth_id)
            prof_data = sim.community.profession_data[profession]
            duration = prof_data.apprenticeship_duration_years
            
            sim.relationships.add_relationship(
                master_id, youth_id, RelationType.APPRENTICE,
                start_time=self.time, duration_years=duration
            )
            
            sim.schedule(GraduateApprenticeshipEvent(
                self.time + duration * 365,
                youth_id, master_id, profession
            ))
            
            for quarter in range(duration * 4):
                sim.schedule(SkillTransferEvent(
                    self.time + quarter * 91.25,
                    youth_id, master_id, profession
                ))
        
        for youth_id in eligible_youth:
            if youth_id not in matched_youth:
                sim.set_person_profession(youth_id, 'farmer')
                
        sim.schedule(CareerMarketEvent(self.time + 365))

    def _find_profession_for_good(self, good: str, sim: 'Simulation') -> Optional[str]:
        for prof, data in sim.community.profession_data.items():
            if data.good_produced == good:
                return prof
        return None

# ============================================================================
# SKILL & GRADUATION EVENTS
# ============================================================================

class SkillTransferEvent(Event):
    """Quarterly skill transfer from master to apprentice (REQ-SP-005)."""
    
    def __init__(
        self, 
        time: float, 
        apprentice_id: int, 
        master_id: int, 
        profession: str
    ):
        super().__init__(time)
        self.apprentice_id = apprentice_id
        self.master_id = master_id
        self.profession = profession
    
    def execute(self, sim: 'Simulation'):
        apprentice = sim.population.get(self.apprentice_id)
        master = sim.population.get(self.master_id)
        
        if not apprentice or not master or \
           not apprentice.is_alive(self.time) or not master.is_alive(self.time):
            return
        
        # Check if relationship is still active
        rels = sim.relationships.get_inbound(self.apprentice_id, RelationType.APPRENTICE, active_at_time=self.time)
        if not any(r[0] == self.master_id for r in rels):
            return # Master died or apprenticeship ended
            
        prof_data = sim.community.profession_data[self.profession]
        skill = prof_data.skill_name
        
        base_hours = 520
        aptitude = apprentice.aptitudes.get(skill, 1.0)
        
        master_hours = master.skill_hours.get(skill, 0)
        master_bonus = 1.0 + min(1.0, master_hours / 10000)
        
        hours_gained = base_hours * aptitude * master_bonus
        apprentice.skill_hours[skill] = \
            apprentice.skill_hours.get(skill, 0) + hours_gained


class GraduateApprenticeshipEvent(Event):
    """
    Complete apprenticeship, end temporal relationship, assign profession.
    v5.0: Calls end_relationship.
    """
    
    def __init__(
        self, 
        time: float, 
        apprentice_id: int, 
        master_id: int, 
        profession: str
    ):
        super().__init__(time)
        self.apprentice_id = apprentice_id
        self.master_id = master_id
        self.profession = profession
    
    def execute(self, sim: 'Simulation'):
        apprentice = sim.population.get(self.apprentice_id)
        
        # End the relationship regardless of liveness to close graph
        sim.relationships.end_relationship(
            self.master_id, self.apprentice_id, RelationType.APPRENTICE, self.time
        )
        
        if not apprentice or not apprentice.is_alive(self.time):
            return
            
        sim.set_person_profession(self.apprentice_id, self.profession)
        
        prof_data = sim.community.profession_data[self.profession]
        if prof_data.building_required:
            owns_one = any(
                b.type == prof_data.building_required and b.owner_id == self.apprentice_id
                for b in sim.buildings_by_owner.get(self.apprentice_id, [])
            )
            if not owns_one:
                building = Building(
                    id=sim.next_building_id(),
                    type=prof_data.building_required,
                    owner_id=self.apprentice_id,
                    built_time=self.time
                )
                sim.add_building(building)

# ============================================================================
# MATCHMAKING STRATEGIES
# ============================================================================

class FamilyPreferenceMatching(MatchmakingStrategy):
    """Default strategy: Match youth to masters, preferring family."""
    
    def match(
        self,
        candidates: List[int],
        masters_by_profession: Dict[str, List[int]],
        slots_by_profession: Dict[str, int],
        sim: 'Simulation'
    ) -> List[Tuple[int, int, str]]:
        
        scores = []
        for profession, slots in slots_by_profession.items():
            masters = masters_by_profession.get(profession, [])
            for youth in candidates:
                for master in masters:
                    score = self._calculate_score(youth, master, profession, sim)
                    scores.append((score, youth, master, profession))
        
        scores.sort(reverse=True, key=lambda x: x[0])
        
        matches = []
        assigned_youth = set()
        assigned_masters = defaultdict(int)
        remaining_slots = slots_by_profession.copy()
        
        for score, youth, master, profession in scores:
            if youth in assigned_youth: continue
            if remaining_slots.get(profession, 0) <= 0: continue
            
            prof_data = sim.community.profession_data[profession]
            if assigned_masters[master] >= prof_data.max_apprentices_per_master:
                continue
            
            matches.append((youth, master, profession))
            assigned_youth.add(youth)
            assigned_masters[master] += 1
            remaining_slots[profession] -= 1
        
        return matches
    
    def _calculate_score(
        self, 
        youth_id: int, 
        master_id: int, 
        profession: str,
        sim: 'Simulation'
    ) -> float:
        score = 0.0
        
        youth_parents = set(sim.relationships.get_parents(youth_id))
        if master_id in youth_parents:
            score += 100
        else:
            master_parents = set(sim.relationships.get_parents(master_id))
            if youth_parents and youth_parents.intersection(master_parents):
                score += 50
        
        prof_data = sim.community.profession_data[profession]
        master_skill = sim.get_skill_level(master_id, prof_data.skill_name)
        score += master_skill / 1000
        
        youth = sim.population[youth_id]
        aptitude = youth.aptitudes.get(prof_data.skill_name, 1.0)
        score += aptitude * 10
        
        return score + sim.rng.random() * 0.1

# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_simulation(sim: Simulation, config_path: str):
    """
    Set up initial population, economy, and events (REQ-IN-001).
    """
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        sim.community.load_config(config)
    except FileNotFoundError:
        print(f"Error: Config file not found at {config_path}")
        return
    except Exception as e:
        print(f"Error loading config: {e}")
        return
    
    p_data = [
        {'id': 1, 'gender': 'male', 'age': 25, 'prof': None, 'skill': 0},
        {'id': 2, 'gender': 'female', 'age': 25, 'prof': None, 'skill': 0},
        {'id': 3, 'gender': 'male', 'age': 25, 'prof': None, 'skill': 0},
        {'id': 4, 'gender': 'female', 'age': 25, 'prof': None, 'skill': 0},
        {'id': 5, 'gender': 'male', 'age': 20, 'prof': 'farmer', 'skill': 10000},
        {'id': 6, 'gender': 'female', 'age': 20, 'prof': 'farmer', 'skill': 10000},
        {'id': 7, 'gender': 'male', 'age': 30, 'prof': 'blacksmith', 'skill': 20000},
        {'id': 8, 'gender': 'male', 'age': 28, 'prof': 'carpenter', 'skill': 20000},
    ]

    for data in p_data:
        person = Person(
            id=data['id'],
            gender=data['gender'],
            birth_time=-data['age'] * 365
        )
        for prof_key in sim.community.profession_data:
            skill_name = sim.community.profession_data[prof_key].skill_name
            person.aptitudes[skill_name] = sim.rng.uniform(0.7, 1.3)
            
        sim.population[person.id] = person
        sim.add_person_to_indices(person)
        
        death_age = sim.rng.gauss(65, 10)
        sim.schedule(DeathEvent(person.birth_time + death_age * 365, person.id))
        
        if data['prof']:
            prof_data = sim.community.profession_data[data['prof']]
            person.skill_hours[prof_data.skill_name] = data['skill']
            sim.set_person_profession(person.id, data['prof'])

    sim.schedule(MarriageEvent(0.0, 1, 2))
    sim.schedule(MarriageEvent(0.0, 5, 6))
    
    b1 = Building(id=1, type='forge', owner_id=7, built_time=-5*365)
    b2 = Building(id=2, type='workshop', owner_id=8, built_time=-5*365)
    sim.add_building(b1)
    sim.add_building(b2)
    
    sim.matchmaking_strategy = FamilyPreferenceMatching()
    
    sim.schedule(UpdateCommunityEconomyEvent(0.1))
    sim.schedule(ResourceStressCheckEvent(0.2))
    sim.schedule(CareerMarketEvent(0.5))
    sim.schedule(ReproductionCheckEvent(1.0))
    sim.schedule(MarriageMarketEvent(1.5))

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == '__main__':
    
    sim = Simulation(seed=42)
    
    CONFIG_FILE = "economy_config.json"
    
    try:
        initialize_simulation(sim, CONFIG_FILE)
        print(f"Successfully initialized simulation with '{CONFIG_FILE}'.")
        
        print(f"Running simulation for 300 years...")
        sim.run(max_time=300 * 365)
        
        print(f"\n--- Simulation Complete at t={sim.time/365.0:.2f} years ---")
        
        if sim.alive_population_count > 0:
            print(f"Final alive population: {sim.alive_population_count}")
            print(f"  Males: {sim.alive_male_count} ({(sim.alive_male_count/sim.alive_population_count)*100:.1f}%)")
            print(f"  Females: {sim.alive_female_count} ({(sim.alive_female_count/sim.alive_population_count)*100:.1f}%)")
        else:
            print("Final alive population: 0 (Extinction)")

        print("\nProfession Counts (Active Practitioners):")
        for profession in sim.community.profession_data.keys():
            good = sim.community.profession_data[profession].good_produced
            if good in sim.community.production:
                count = sim.community.production[good].current_practitioners
                print(f"  {profession}: {count}")
            
        print("\nMarket Gaps (Demand/Supply):")
        for good, gap in sim.community.market_gaps.items():
            print(f"  {good}: {gap:.2f}")

    except FileNotFoundError:
        print(f"Fatal Error: '{CONFIG_FILE}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
