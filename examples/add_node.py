from neo4j import GraphDatabase, basic_auth
import nxneo4j
import networkx as nx

driver = GraphDatabase.driver("bolt://localhost:7687")

config = {
    "node_label": "Food",
    "relationship_type": "CONTAINS",
    "identifier_property": "name"
}
G = nxneo4j.Graph(driver, config)
H = nx.Graph()
H.add_node("Cherry", shape="curved")

G.clear()
G.add_node("Apple", shape="round")
G.add_node("Banana", {
    "shape": "curved",
    "average_weight": 100
})
G.add_node("Citrus")
G.remove_node("Apple")
G.add_nodes_from(["Peach", "Lemon"], tropic=True)
G.remove_nodes_from(["Peach", "Citrus"])
G.add_nodes_from([("Pear", {
    "shape": None,
    "average_weight": 200
}), ("Apricot", {
    "shape": "round"
})])
G.add_nodes_from(H.nodes(data=True), imported=True)

for name, properties in G.nodes(data=True):
    print("{} has {} properties".format(name, len(properties)))
    for k, v in properties.items():
        print("\t{}:\t{}".format(k, v))
