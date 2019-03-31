from neo4j.v1 import GraphDatabase, basic_auth
import nxneo4j

driver = GraphDatabase.driver("bolt://localhost:7687")

config = {
    "node_label": "Person",
    "relationship_type": None,
    "identifier_property": "name"
}
G = nxneo4j.Graph(driver, config)

for n in G.nodes:
    print(n)

for name, salary in G.nodes(data="salary", default=0):
    print("{} earns ${} each month".format(name, salary))

for name, properties in G.nodes(data=True):
    print("{} has {} properties".format(name, len(properties)))
    for k, v in properties.items():
        print("\t{}:\t{}".format(k, v))
