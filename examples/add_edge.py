from neo4j import GraphDatabase, basic_auth
import nxneo4j
import networkx as nx

driver = GraphDatabase.driver("bolt://localhost:7687")

config = {
    "node_label": "Food",
    "relationship_type": "CONTAINS",
    "identifier_property": "name"
}
G = nxneo4j.DiGraph(driver, config)
H = nx.DiGraph()
H.add_node(777, name="Cherry", shape="curved")
H.add_node(888, name="Cherry juice")
H.add_edge("Cherry juice", "Cherry", percentage=100)
H.add_node(123, name="Kiwi")

G.clear()
# G.add_node("Apple", shape="round")
G.add_node("Banana", {
    "shape": "curved",
    "average_weight": 100
})
G.add_edge("Apple-banana juice", "Apple", percentage=60)
G.add_edge("Apple-banana juice", "Banana", percentage=40)
G.add_path(["Fish and Chips", "Pommes", "Potato"])
G.add_node("Citrus")
G.add_nodes_from([("Pear", {
    "shape": None,
    "average_weight": 200
}), ("Apricot", {
    "shape": "round"
})])

# G.update(H) does the same as:
# G.add_nodes_from(H.nodes(data=True))
# G.add_edges_from(H.edges(data=True))
# graph_id_props allows us to specify properties, where to save the original nx node
G.update(H, graph_id_props="original_id")

for name, properties in G.nodes(data=True):
    print("{} has {} properties".format(name, len(properties)))
    for k, v in properties.items():
        print("\t{}:\t{}".format(k, v))

for u, v in G.edges:
    print("{} contains {}".format(u, v))

for u, v, properties in G.edges(data=True):
    print("{} contains {} with those properties:".format(u, v))
    for k, v in properties.items():
        print("\t{}:\t{}".format(k, v))
