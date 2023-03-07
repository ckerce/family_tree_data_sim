import networkx as nx
import matplotlib.pyplot as plt


def plot_family_tree(data):
   # Create a new directed graph
   G = nx.DiGraph()

   # Add nodes for each person
   for person in data:
       G.add_node(person['name'])

   # Add edges for parent, spouse, and cousin relationships
   for person in data:
       if 'father' in person:
           G.add_edge(person['father'], person['name'],color='k')
       if 'mother' in person:
           G.add_edge(person['mother'], person['name'],color='k')
       if 'spouse' in person:
           G.add_edge(person['name'], person['spouse'],color='r')
       if 'cousins' in person:
           for dat in person['cousins']:
               G.add_edge(dat, person['name'],color='b',weight=18)

   # Draw the graph
   colors = nx.get_edge_attributes(G,'color').values()
   pos = nx.kamada_kawai_layout(G)
   nx.draw_networkx_nodes(G, pos, node_size=500)
   nx.draw_networkx_labels(G, pos, {person['name']: person['name'] for person in data})
   nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color=colors)
   plt.axis('off')
   plt.show()

if __name__ == '__main__':
   
   # Define the data as a list of dictionaries
   data = [
       {"name": 478, "gender": "female", "birth_year": 949, "father": 455, "mother": 450, "grandfather": 436, "grandmother": 435, "siblings": [473], "cousins": [472, 476, 474, 477, 480, 488, 482, 493, 475, 479]},
       {"name": 479, "gender": "female", "birth_year": 953, "father": 460, "mother": 446, "grandfather": 436, "grandmother": 434, "siblings": [475], "cousins": [467, 473, 478]},
       {"name": 480, "gender": "female", "birth_year": 954, "spouse": 484, "father": 456, "mother": 457, "grandfather": 433, "grandmother": 435, "children": [502, 504], "siblings": [474, 477, 488], "cousins": [472, 476, 473, 478, 482, 493, 463, 471, 466, 469, 470, 486]},
       {"name": 481, "gender": "male", "birth_year": 957, "spouse": 477, "father": 463, "mother": 454, "grandfather": 445, "grandmother": 444, "children": [497, 498, 499], "siblings": [484], "cousins": [483, 489, 491, 485, 490, 495]},
       {"name": 482, "gender": "female", "birth_year": 958, "father": 465, "mother": 464, "grandfather": 443, "grandmother": 439, "siblings": [493], "cousins": [472, 476, 473, 478, 474, 477, 480, 488, 486]}
   ]

   plot_family_tree(data)
