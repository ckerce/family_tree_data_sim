import random
import json

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
        self.birthyear = year 
        self.deathyear = None 
        self.alive = True
        
    def marry(self, spouse):
        if self.spouse == None:
           self.spouse = spouse
           spouse.marry( self )
        
    def add_child(self, child):
        self.children.append(child)

    def age(self,t):
        return t - self.birthyear


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
    

# create initial community
p = []
idx = 0
p.append( Person(idx, "male") )
idx +=1
p.append( Person(idx, "female") )
idx +=1
p.append( Person(idx, "male") )
idx +=1
p.append( Person(idx, "female") )
idx +=1
p.append( Person(idx, "male") )
idx +=1
p.append( Person(idx, "female") )
idx +=1
p.append( Person(idx, "male") )
idx +=1
p.append( Person(idx, "female") )
idx +=1
p.append( Person(idx, "male") )
idx +=1
p.append( Person(idx, "female") )

# Make sure that at least two married couples exist in the initial population
p[0].marry( p[1] )
p[2].marry( p[3] )


birth_probability = 0.5
marriage_probability = 0.1
for t in range(300):
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

# Fill out grandparent relationships 
for person in p:
    for c in person.children:
        for cc in c.children:
            if person.gender == "female":
                cc.grandmother = person
            else:
                cc.grandfather = person

# TODO: Fill out sibling relationships
# TODO: Fill out cousin relationships


a = []
for person in p: 
    if person.age(t) < 240: 
        a.append(person)

for person in a:
    #print_family(person)
    print( create_family_json(person) )
