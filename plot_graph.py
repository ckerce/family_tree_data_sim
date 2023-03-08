import networkx as nx
import matplotlib.pyplot as plt
import pydot
from networkx.drawing.nx_pydot import graphviz_layout


def plot_family_tree(data):
   # Create a new directed graph
   G = nx.DiGraph()

   # Add nodes for each person
   for person in data:
       G.add_node(person['name'])

   # Add edges for parent and spouse relationships
   for person in data:
       if 'father' in person:
           G.add_edge(person['father'], person['name'],color='k')
       if 'mother' in person:
           G.add_edge(person['mother'], person['name'],color='k')

   #pos = graphviz_layout(G, prog='twopi')
   pos = graphviz_layout(G, prog='dot')
   colors = nx.get_edge_attributes(G,'color').values()
   nx.draw_networkx_nodes(G, pos, node_size=500)
   nx.draw_networkx_labels(G, pos, {person['name']: person['name'] for person in data},)
   #pos = nx.circular_layout(G)
   #pos = nx.kamada_kawai_layout(G)
   #pos = nx.planar_layout(G)

   #for person in data:
   #    if 'spouse' in person:
   #        G.add_edge(person['name'], person['spouse'],color='r')
   #    if 'cousins' in person:
   #        for dat in person['cousins']:
   #            G.add_edge(dat, person['name'],color='b',weight=18)

   # Draw the graph using a circular layout
   #nx.draw_networkx_nodes(G, pos, node_size=500)
   nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color=colors)
   plt.axis('off')
   plt.show()
   return G

if __name__ == '__main__':
   
   # Define the data as a list of dictionaries
   data = [
           {"name": 'Fleur Delacour', "spouse": 'Bill Weasley', "children": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley']},
           {"name": 'Victoire Weasley', "father": 'Bill Weasley', "mother": 'Fleur Delacour', "siblings": ['Dominique Weasley', 'Louis Weasley'], "cousins": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Rose Granger-Weasley', 'Hugo Granger-Weasley', 'Fred Weasley II', 'Roxanne Weasley']},
           {"name": 'Dominique Weasley', "father": 'Bill Weasley', "mother": 'Fleur Delacour', "siblings": ['Victoire Weasley', 'Louis Weasley'], "cousins": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Rose Granger-Weasley', 'Hugo Granger-Weasley', 'Fred Weasley II', 'Roxanne Weasley']},
           {"name": 'Louis Weasley', "father": 'Bill Weasley', "mother": 'Fleur Delacour', "siblings": ['Victoire Weasley', 'Dominique Weasley'], "cousins": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Rose Granger-Weasley', 'Hugo Granger-Weasley', 'Fred Weasley II', 'Roxanne Weasley']},
           {"name": 'Fred Weasley II', "father": 'George Weasley', "mother": 'Angelina Johnson', "siblings": ['Roxanne Weasley'], "cousins": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley', 'James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Rose Granger-Weasley', 'Hugo Granger-Weasley']},
           {"name": 'Roxanne Weasley', "father": 'George Weasley', "mother": 'Angelina Johnson', "siblings": ['Fred Weasley II'], "cousins": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley', 'James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Rose Granger-Weasley', 'Hugo Granger-Weasley']},
           {"name": 'Rose Granger-Weasley', "father": 'Ron Weasley', "mother": 'Hermione Granger', "siblings": ['Hugo Granger-Weasley'], "cousins": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley', 'James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Fred Weasley II', 'Roxanne Weasley']},
           {"name": 'Hugo Granger-Weasley', "father": 'Ron Weasley', "mother": 'Hermione Granger', "siblings": ['Rose Granger-Weasley'], "cousins": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley', 'James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Fred Weasley II', 'Roxanne Weasley']},
           {"name": 'James Potter', "gender": "male", "birth_year": 1960, "death_year": 1981, "spouse": 'Lily Evans', "father": 'Fleamont Potter', "mother": 'Euphemia Potter', "children": ['Harry Potter'], "cousins": []},
           {"name": 'Lily Evans', "gender": "female", "birth_year": 1960, "death_year": 1981, "spouse": 'James Potter', "parents": ['Mr. Evans', 'Mrs. Evans'], "children": ['Harry Potter'], "cousins": []},
           {"name": 'Harry Potter', "gender": "male", "birth_year": 1980, "spouse": 'Ginny Weasley', "father": 'James Potter', "mother": 'Lily Evans', "children": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter'], "cousins": ['Dudley Dursley']},
           {"name": 'Arthur Weasley', "gender": "male", "birth_year": 1950, "spouse": 'Molly Weasley', "children": ['Bill Weasley', 'Charlie Weasley', 'Percy Weasley', 'Fred Weasley', 'George Weasley', 'Ron Weasley', 'Ginny Weasley'], "cousins": []},
           {"name": 'Molly Weasley', "gender": "female", "birth_year": 1949, "spouse": 'Arthur Weasley', "children": ['Bill Weasley', 'Charlie Weasley', 'Percy Weasley', 'Fred Weasley', 'George Weasley', 'Ron Weasley', 'Ginny Weasley'], "cousins": []},
           {"name": 'Bill Weasley', "gender": "male", "birth_year": 1970, "spouse": 'Fleur Delacour', "father": 'Arthur Weasley', "mother": 'Molly Weasley', "children": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley'], "cousins": []},
           {"name": 'Percy Weasley', "gender": "male", "birth_year": 1976, "spouse": 'Audrey Weasley', "father": 'Arthur Weasley', "mother": 'Molly Weasley', "children": ['Molly Weasley II', 'Lucy Weasley']},
           {"name": 'Audrey Weasley', "gender": "female", "birth_year": 1978, "spouse": 'Percy Weasley', "children": ['Molly Weasley II', 'Lucy Weasley']},
           {"name": 'Molly Weasley II', "gender": "female", "birth_year": 2008, "father": 'Percy Weasley', "mother": 'Audrey Weasley'},
           {"name": 'Lucy Weasley', "gender": "female", "birth_year": 2010, "father": 'Percy Weasley', "mother": 'Audrey Weasley'},
           {"name": 'Bill Weasley', "gender": "male", "birth_year": 1970, "spouse": 'Fleur Delacour', "father": 'Arthur Weasley', "mother": 'Molly Weasley', "children": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley']},
           {"name": 'Fleur Delacour', "gender": "female", "birth_year": 1977, "spouse": 'Bill Weasley', "children": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley']},
           {"name": 'Victoire Weasley', "gender": "female", "birth_year": 2000, "father": 'Bill Weasley', "mother": 'Fleur Delacour'},
           {"name": 'Dominique Weasley', "gender": "female", "birth_year": 2002, "father": 'Bill Weasley', "mother": 'Fleur Delacour'},
           {"name": 'Louis Weasley', "gender": "male", "birth_year": 2005, "father": 'Bill Weasley', "mother": 'Fleur Delacour'},
           {"name": 'Ginny Weasley', "gender": "female", "birth_year": 1981, "spouse": 'Harry Potter', "father": 'Arthur Weasley', "mother": 'Molly Weasley', "siblings": ['Bill Weasley', 'Charlie Weasley', 'Percy Weasley', 'Fred Weasley', 'George Weasley', 'Ron Weasley'], "children": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter']},
           {"name": 'George Weasley', "gender": "male", "birth_year": 1978, "death_year": 'UNK', "father": 'Arthur Weasley', "mother": 'Molly Weasley', "siblings": ['Fred Weasley'], "spouse": 'Angelina Johnson', "children": ['Fred Weasley II', 'Roxanne Weasley'], "cousins": []},
           {"name": 'Angelina Johnson', "gender": "female", "birth_year": 1977, "death_year": 'UNK', "father": 'UNK', "mother": 'UNK', "siblings": [], "spouse": 'George Weasley', "children": ['Fred Weasley II', 'Roxanne Weasley'], "cousins": []},
           {"name": 'Fred Weasley II', "gender": "male", "birth_year": 2004, "death_year": 'UNK', "father": 'George Weasley', "mother": 'Angelina Johnson', "siblings": ['Roxanne Weasley'], "cousins": []},
           {"name": 'Roxanne Weasley', "gender": "female", "birth_year": 2007, "death_year": 'UNK', "father": 'George Weasley', "mother": 'Angelina Johnson', "siblings": ['Fred Weasley II'], "cousins": []},
           {"name": 'Charlie Weasley', "gender": "male", "birth_year": 1972, "death_year": 'UNK', "father": 'Arthur Weasley', "mother": 'Molly Weasley', "siblings": ['Bill Weasley', 'Charlie Weasley', 'Percy Weasley', 'Fred Weasley', 'George Weasley', 'Ron Weasley', 'Ginny Weasley'], "cousins": ['Nymphadora Tonks', 'Fred Weasley II', 'Roxanne Weasley', 'Rose Weasley', 'Hugo Weasley', 'James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter']},
           {"name": 'Vernon Dursley', "gender": "male", "birth_year": 'UNK', "death_year": 'UNK', "father": 'UNK', "mother": 'UNK', "siblings": [], "cousins": []},
           {"name": 'Petunia Dursley', "gender": "female", "birth_year": 'UNK', "death_year": 2020, "father": 'Mr. Evans', "mother": 'Mrs. Evans', "siblings": ['Lily Potter'], "cousins": []},
           {"name": 'Dudley Dursley', "gender": "male", "birth_year": 1980, "death_year": 'UNK', "father": 'Vernon Dursley', "mother": 'Petunia Dursley', "siblings": [], "cousins": ['Harry Potter']},
           {"name": 'Fred Weasley II', "gender": "male", "birth_year": 2004, "death_year": 'UNK', "father": 'George Weasley', "mother": 'Angelina Johnson', "siblings": ['Roxanne Weasley'], "cousins": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Victoire Weasley', 'Dominique Weasley', 'Louis Weasley']} ,           
           {"name": 'Roxanne Weasley', "gender": "female", "birth_year": 2005, "death_year": 'UNK', "father": 'George Weasley', "mother": 'Angelina Johnson', "siblings": ['Fred Weasley II'], "cousins": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Victoire Weasley', 'Dominique Weasley', 'Louis Weasley']} ,           
           {"name": 'Rose Weasley', "gender": "female", "birth_year": 2006, "death_year": 'UNK', "father": 'Ron Weasley', "mother": 'Hermione Granger', "siblings": ['Hugo Weasley'], "cousins": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Victoire Weasley', 'Dominique Weasley', 'Louis Weasley', 'Molly Weasley II', 'Lucy Weasley', 'Fred Weasley II', 'Roxanne Weasley']} ,           
           {"name": 'Hugo Weasley', "gender": "male", "birth_year": 2008, "death_year": 'UNK', "father": 'Ron Weasley', "mother": 'Hermione Granger', "siblings": ['Rose Weasley'], "cousins": ['James Sirius Potter', 'Albus Severus Potter', 'Lily Luna Potter', 'Victoire Weasley', 'Dominique Weasley', 'Louis Weasley', 'Molly Weasley II', 'Lucy Weasley', 'Fred Weasley II', 'Roxanne Weasley']} ,           
           {"name": 'James Sirius Potter', "gender": "male", "birth_year": 2004, "death_year": 'UNK', "father": 'Harry Potter', "mother": 'Ginny Weasley', "siblings": ['Albus Severus Potter', 'Lily Luna Potter'], "cousins": ['Victoire Weasley', 'Dominique Weasley', 'Louis Weasley', 'Molly Weasley II', 'Lucy Weasley', 'Fred Weasley II', 'Roxanne Weasley', 'Rose Weasley', 'Hugo Weasley']} ,           
           {"name": 'Albus Severus Potter', "gender": "male", "birth_year": 2006, "father": 'Harry Potter', "mother": 'Ginny Weasley', "siblings": ['James Sirius Potter', 'Lily Luna Potter'], "cousins": ['Rose Weasley', 'Hugo Weasley', 'Fred Weasley II', 'Roxanne Weasley']} ,           
           {"name": 'Lily Luna Potter', "gender": "female", "birth_year": 2008, "father": 'Harry Potter', "mother": 'Ginny Weasley', "siblings": ['James Sirius Potter', 'Albus Severus Potter'], "cousins": ['Rose Weasley', 'Hugo Weasley', 'Fred Weasley II', 'Roxanne Weasley']} ,
           {"name": 'Nymphadora Tonks', "gender": "female", "birth_year": 1973, "death_year": 1998, "father": 'Ted Tonks', "mother": 'Andromeda Tonks', "siblings": [], "cousins": ['Draco Malfoy', 'Bellatrix Lestrange', 'Narcissa Malfoy']},
           {"name": 'Andromeda Tonks', "gender": "female", "birth_year": 1951, "death_year": 'UNK', "father": 'Cygnus Black III', "mother": 'Druella Rosier', "siblings": ['Bellatrix Lestrange', 'Narcissa Malfoy'], "cousins": ['Sirius Black', 'Regulus Black']} ,
           {"name": 'Ted Tonks', "gender": "male", "birth_year": 1950, "death_year": 1998, "father": 'UNK', "mother": 'UNK', "siblings": [], "cousins": ['Sirius Black']} ,
           {"name": 'Sirius Black', "gender": "male", "birth_year": 1959, "death_year": 1996, "father": 'Orion Black', "mother": 'Walburga Black', "siblings": ['Regulus Black'], "cousins": ['Andromeda Tonks', 'Narcissa Malfoy', 'Bellatrix Lestrange', 'Ted Tonks']} ,
           {"name": 'Regulus Black', "gender": "male", "birth_year": 1961, "death_year": 1979, "father": 'Orion Black', "mother": 'Walburga Black', "siblings": ['Sirius Black'], "cousins": ['Andromeda Tonks', 'Narcissa Malfoy', 'Bellatrix Lestrange', 'Ted Tonks']} ,
           {"name": 'Bellatrix Lestrange', "gender": "female", "birth_year": 1951, "death_year": 1998, "father": 'Cygnus Black III', "mother": 'Druella Rosier', "siblings": ['Andromeda Tonks', 'Narcissa Malfoy'], "cousins": ['Sirius Black', 'Regulus Black']} ,
           {"name": 'Narcissa Malfoy', "gender": "female", "birth_year": 1955, "death_year": 'UNK', "father": 'Cygnus Black III', "mother": 'Druella Rosier', "siblings": ['Bellatrix Lestrange', 'Andromeda Tonks'], "cousins": ['Sirius Black', 'Regulus Black']} ,
           {"name": 'Draco Malfoy', "gender": "male", "birth_year": 1980, "death_year": 'UNK', "father": 'Lucius Malfoy', "mother": 'Narcissa Malfoy', "siblings": ['UNK'], "cousins": ['Bellatrix Lestrange']}

        ]

   G = plot_family_tree(data)
