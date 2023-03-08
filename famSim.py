import random
import json

def create_family_json(person):
    family_dict = {
        "name": person.name,
        "gender": person.gender,
        "birth_year": person.birthyear
    }
    
    if person.deathyear:
        family_dict["death_year"] = person.deathyear
    if person.spouse:
        family_dict["spouse"] = person.spouse.name
    if person.father:
        family_dict["father"] = person.father.name
    if person.mother:
        family_dict["mother"] = person.mother.name
    if person.grandfather:
        family_dict["grandfather"] = person.grandfather.name
    if person.grandmother:
        family_dict["grandmother"] = person.grandmother.name
    if person.children:
        family_dict["children"] = [child.name for child in person.children]
    if person.siblings:
        family_dict["siblings"] = [sibling.name for sibling in person.siblings]
    if person.cousins:
        family_dict["cousins"]  = [cousin.name for cousin in person.cousins]
    if person.aunts:
        family_dict["aunts"]  = [aunt.name for aunt in person.aunts]
    if person.uncles:
        family_dict["uncles"]  = [uncle.name for uncle in person.uncles]
    if person.nephews:
        family_dict["nephews"]  = [nephew.name for nephew in person.nephews]
    if person.nieces:
        family_dict["nieces"]  = [niece.name for niece in person.nieces]
    
    return json.dumps(family_dict)


def print_family(person): 
    print("Name:", person.name) 
    print("   Gender:", person.gender) 
    print("   Birth Year:", person.birthyear) 
    print("   Death Year:", person.deathyear) 
    if person.spouse: 
        print("   Spouse:", person.spouse.name) 
    if person.father: 
        print("   Father:", person.father.name) 
    if person.mother: 
        print("   Mother:", person.mother.name) 
    if person.grandfather: 
        print("   Grandfather:", person.grandfather.name) 
    if person.grandmother: 
        print("   Grandmother:", person.grandmother.name) 
    if person.children: 
        #print("Children:") 
        for child in person.children: 
            print("   Child", child.name) 
    
def count_alive(a): 
  mysum = 0 
  for person in a: 
    if person.alive: 
        mysum += 1 
  return mysum


class Person:
    def __init__(self, name, gender, year=0):
        self.name = name
        self.gender = gender
        self.spouse = None
        self.father = random.random()
        self.mother = random.random()
        self.grandmother = random.random()
        self.grandfather = random.random()
        self.children = []
        self.siblings = []
        self.cousins = []
        self.uncles = []
        self.aunts = []
        self.nephews = []
        self.nieces = []
        self.birthyear = year
        self.deathyear = None
        self.alive = True

    def marry(self, spouse):
        if self.spouse == None:
           self.spouse = spouse
           spouse.marry( self )

    def add_child(self, child):
        self.children.append(child)

    def add_sibling(self, sibling):
        if sibling not in self.siblings:
            self.siblings.append(sibling)
            sibling.add_sibling(self)

    def add_cousin(self, cousin):
        if cousin not in self.cousins:
            self.cousins.append(cousin)
            cousin.add_cousin(self)

    def add_uncle(self, uncle):
        if uncle not in self.uncles:
            self.uncles.append(uncle)

    def add_aunt(self, aunt):
        if aunt not in self.aunts:
            self.aunts.append(aunt)

    def add_nephew(self, nephew):
        if nephew not in self.nephews:
            self.nephews.append(nephew)

    def add_niece(self, niece):
        if niece not in self.nieces:
            self.nieces.append(niece)

    def age(self,t):
        return t - self.birthyear

#class Person:
#    def __init__(self, name, gender, year=0):
#        self.name = name
#        self.gender = gender
#        self.spouse = None
#        self.father = random.random() 
#        self.mother = random.random() 
#        self.grandmother = random.random() 
#        self.grandfather = random.random() 
#        self.children = []
#        self.birthyear = year 
#        self.deathyear = None 
#        self.alive = True
#        
#    def marry(self, spouse):
#        if self.spouse == None:
#           self.spouse = spouse
#           spouse.marry( self )
#        
#    def add_child(self, child):
#        self.children.append(child)
#
#    def age(self,t):
#        return t - self.birthyear

def fill_sibling_relationships(p):
    # siblings have a common parent, so start from parents 
    # and drill down one level.  Double loop over all children
    # but don't count a person as their own sibling.
    for person in p:
        for child in person.children:
            for sibling in person.children:
                if child != sibling:
                    child.add_sibling(sibling)

def fill_cousin_relationships(p):
    # cousins have common grandparents, but not common parents.
    # Start from grandparents and drill down two levels.
    # a sibling of a person can not be their cousin.
    for grand_person in p:
        for parent in grand_person.children:
            for sibling_parent in grand_person.children:
                if parent != sibling_parent:
                    for target_child in parent.children:
                        for cousin in sibling_parent.children:
                            target_child.add_cousin(cousin)

def fill_aunt_or_uncle_relationship(p):
    # aunt_uncle is a sibling of child's parent
    for person in p:
        for sibling in person.siblings:
            for child in person.children:
               if sibling.gender == "male":
                   child.add_uncle(sibling)
               elif sibling.gender == "female":
                   child.add_aunt(sibling)
               else:
                   print("Gender error")

def fill_niece_or_nephew_relationship(p):
    # aunt_uncle is a sibling of child's parent
    for person in p:
        for sibling in person.siblings:
            for child in person.children:
               if child.gender == "male":
                   sibling.add_nephew(child)
               elif child.gender == "female":
                   sibling.add_niece(child)
               else:
                   print("Gender error")

# create initial community
def create_initial_population():
   p = []
   for idx in range(4):
      p.append( Person(2*idx, "male") )
      p.append( Person(2*idx+1, "female") )
   
   # Make sure that at least two married couples exist in the initial population
   p[0].marry( p[1] )
   p[2].marry( p[3] )
   return p


random.seed(10)
birth_probability = 0.32
marriage_probability = 0.1

p = []
out = []
while len(p) < 750 and count_alive(p) < 10:
   p = create_initial_population()
   counts = []
   for t in range(1000):
       # For each female in population p, check to see if 
       # 1. that person # is greater than 20 years old and less than 50 years old.  
       # 2. that the person has a male spouse
       # When these two conditions are true, assign a birth with probability birth_probability 
       for person in p:
           cur_birth_prob = birth_probability / (1 + 2*len(person.children))
           if person.alive and person.gender == "female" and person.age(t) > 20 and person.age(t) < 50 and person.spouse != None and random.random() < cur_birth_prob and len(person.children) < 8:
               child = Person(len(p), random.choice(["male", "female"]), t)
               child.mother = person
               child.father = person.spouse
               person.add_child(child)
               person.spouse.add_child(child)
               p.append(child)
   
       # For each female in the population, check to see if that person is greater than 20 years old
       # If so, search over all males and marry that female to the first unmarried male 
       for female in p:
           if female.alive and female.gender == "female" and female.age(t) > 20 and female.spouse == None and random.random() < marriage_probability:
               for male in reversed(p):
                   # Make sure immediate family relationship conventions are not violated in marriage.
                   if male.alive and male.gender == "male" and male.spouse == None and male.age(t) > 20 and female.father != male and female.mother != male.mother and female.father != male.father:
                       female.marry(male)
                       break
   
       # Eventually a person has to die.  Everyone dies at age 81 in this population.
       for person in p:
           if person.alive and person.age(t) > 80:
               person.alive = False
               person.deathyear = t
       counts.append(count_alive(p))
   
   # Fill out grandparent relationships 
   for person in p:
       for c in person.children:
           for cc in c.children:
               if person.gender == "female":
                   cc.grandmother = person
               else:
                   cc.grandfather = person
   out.append(counts)
   
   # Fill out sibling relationships
   fill_sibling_relationships(p)
   # TODO: Fill out cousin relationships ... I'm not convinced this works
   fill_cousin_relationships(p)
   # Fill out aunt and uncle relationships
   fill_aunt_or_uncle_relationship(p)
   fill_niece_or_nephew_relationship(p)


a = []
for person in p: 
    if person.age(t) < 240: 
        a.append(person)

for person in a:
    #print_family(person)
    print( create_family_json(person) )
