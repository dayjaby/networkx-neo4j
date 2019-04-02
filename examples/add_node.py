from neo4j.v1 import GraphDatabase, basic_auth
import nxneo4j

driver = GraphDatabase.driver("bolt://localhost:7687")

config = {
    "node_label": "Food",
    "relationship_type": None,
    "identifier_property": "name"
}
G = nxneo4j.Graph(driver, config)

G.clear()
G.add_node("Apple", shape="round")
G.add_node("Banana", {
    "shape": "curved",
    "average_weight": 100
})
G.add_node("Citrus")

for name, properties in G.nodes(data=True):
    print("{} has {} properties".format(name, len(properties)))
    for k, v in properties.items():
        print("\t{}:\t{}".format(k, v))
