import pytest
from neo4j import GraphDatabase, basic_auth
import nxneo4j
import networkx as nx
from networkx.exception import NetworkXError

driver = GraphDatabase.driver("bolt://localhost:7687")

config = {
    "node_label": "Food",
    "relationship_type": "CONTAINS",
    "identifier_property": "name"
}

G = nxneo4j.Graph(driver, config)

def test_clear():
    G.clear()
    assert len(G) == 0
    assert len(G.edges) == 0

def test_add_node():
    G.clear()
    G.add_node("Strawberry", color="red")
    assert len(G) == 1
    assert len(G.edges) == 0
    G.add_node("Blackberry", color="black")
    assert len(G) == 2
    G.add_node("Strawberry", sweet=True)
    assert len(G) == 2

def test_remove_node():
    G.clear()
    G.add_node("Strawberry", color="red")
    G.remove_node("Strawberry")
    assert len(G) == 0
    with pytest.raises(NetworkXError):
        G.remove_node("Strawberry")

def test_nodeview():
    G.clear()
    G.add_node("Apple", shape="round")
    assert len(G) == 1
    assert len(G.edges) == 0
    assert G.nodes["Apple"]["shape"] == "round"
    for n in G.nodes:
        assert n == "Apple"
    node, data = list(G.nodes(data=True))[0]
    assert node == "Apple"
    assert data["shape"] == "round"
    node, shape = list(G.nodes(data="shape"))[0]
    assert node == "Apple"
    assert shape == "round"
    node = list(G.nodes())[0]
    assert node == "Apple"

"""
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
H = nx.Graph()
H.add_node("Cherry", shape="curved")
G.add_nodes_from(H.nodes(data=True), imported=True)

for name, properties in G.nodes(data=True):
    print("{} has {} properties".format(name, len(properties)))
    for k, v in properties.items():
        print("\t{}:\t{}".format(k, v))
        """
