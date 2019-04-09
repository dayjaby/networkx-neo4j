class NodeView:
    def __init__(self, graph):
        self.graph = graph

    def __iter__(self):
        return iter(self.__call__())

    def __call__(self, data=False, default=None):
        with self.graph.driver.session() as session:
            query = self.graph.get_nodes_query % (self.graph.node_label)
            nodes = [r["node"] for r in session.run(query).records()]
            key = self.graph.identifier_property
            if not data:
                for n in nodes:
                    yield n[key]
            elif isinstance(data, bool):
                for n in nodes:
                    rdata = {k: n[k] for k in n.keys() if k!=key}
                    yield (n[key], rdata)
            else:
                for n in nodes:
                    yield n[key], n.get(data, default)

class EdgeView:
    def __init__(self, graph):
        self.graph = graph

    def __iter__(self):
        return iter(self.__call__())

    def __call__(self, data=False, default=None):
        if self.graph.relationship_type is None:
            return # raises StopIteration

        with self.graph.driver.session() as session:
            query = self.graph.get_edges_query % (
                self.graph.node_label,
                self.graph.relationship_type,
                self.graph.node_label,
                self.graph.identifier_property,
                self.graph.identifier_property
            )
            edges = [(r["u"], r["v"], r["edge"]) for r in session.run(query).records()]
            if not data:
                for u, v, _ in edges:
                    yield (u, v)
            elif isinstance(data, bool):
                for u, v, d in edges:
                    yield (u, v, d)
            else:
                for u, v, d in edges:
                    yield (u, v, d.get(data, default))

class BaseGraph:
    def __init__(self, driver, direction, config=None):
        if config is None:
            config = {}

        self.driver = driver
        self.direction = direction
        self.node_label = config.get("node_label", "Node")
        self.node_label_out = config.get("node_label_out", self.node_label)
        self.relationship_type = config.get("relationship_type", "CONNECTED")
        self.graph = config.get("graph", "heavy")
        self.identifier_property = config.get("identifier_property", "id")

    def __iter__(self):
        return iter(self.nodes)

    def __contains__(self, n):
        return n in self.nodes

    def __len__(self):
        return len(self)

    @property
    def nodes(self):
        # Lazy View creation, like in networkx
        nodes = NodeView(self)
        self.__dict__["nodes"] = nodes
        return nodes

    @property
    def edges(self):
        edges = EdgeView(self)
        self.__dict__["edges"] = edges
        return edges

    get_nodes_query = """\
    MATCH (node:`%s`)
    RETURN node
    """

    get_edges_query = """\
    MATCH (u:`%s`)-[edge:`%s`]->(v:`%s`)
    RETURN u.`%s` AS u, v.`%s` AS v, edge
    """

    add_node_query = """\
    MERGE (:`%s` {`%s`: {value} })
    """

    add_node_query_with_props = """\
    MERGE (n:`%s` {`%s`: {value} })
    ON CREATE SET n+=$props
    """
    def add_node(self, value, attr_dict=dict(), **attr):
        with self.driver.session() as session:
            if len(attr_dict) == 0 and len(attr) == 0:
                query = self.add_node_query % (self.node_label, self.identifier_property)
                session.run(query, {"value": value})
            else:
                props = dict(attr_dict)
                for k, v in attr.items():
                    props[k] = v
                query = self.add_node_query_with_props % (self.node_label, self.identifier_property)
                session.run(query, {"value": value}, props=props)

    add_nodes_query = """\
    UNWIND {values} AS value
    MERGE (:`%s` {`%s`: value })
    """

    add_nodes_query_with_attrdict = """\
    UNWIND {values} AS props
    MERGE (n:`%s` {`%s`: props.`%s` })
    ON CREATE SET n=props
    """

    def add_nodes_from(self, values):
        are_node_attrdict_tuple = False
        try:
            for v in values:
                if isinstance(v[1], dict):
                    are_node_attrdict_tuple = True
                break
        except:
            pass

        with self.driver.session() as session:
            if are_node_attrdict_tuple:
                query = self.add_nodes_query_with_attrdict % (
                    self.node_label,
                    self.identifier_property,
                    self.identifier_property
                )
                n_values = []
                for i, d in values:
                    d = dict(d)
                    if self.identifier_property not in d:
                        d[self.identifier_property] = i
                    n_values.append(d)
                values = n_values
            else:
                query = self.add_nodes_query % (self.node_label, self.identifier_property)

            session.run(query, {"values": values})

    add_edge_query = """\
    MERGE (node1:`%s` {`%s`: {node1} })
    MERGE (node2:`%s` {`%s`: {node2} })
    MERGE (node1)-[r:`%s`]->(node2)
    ON CREATE SET r=$props
    """

    def add_edge(self, node1, node2, **attr):
        with self.driver.session() as session:
            query = self.add_edge_query % (
                self.node_label,
                self.identifier_property,
                self.node_label,
                self.identifier_property,
                self.relationship_type
            )
            session.run(query, {"node1": node1, "node2": node2}, props=attr)

    add_edges_query = """\
    UNWIND {edges} AS edge
    MERGE (node1:`%s` {`%s`: edge[0] })
    MERGE (node2:`%s` {`%s`: edge[1] })
    MERGE (node1)-[r:`%s`]->(node2)
    ON CREATE SET r=edge[2]
    """

    def add_edges_from(self, edges, **attr):
        with self.driver.session() as session:
            query = self.add_edges_query % (
                self.node_label,
                self.identifier_property,
                self.node_label,
                self.identifier_property,
                self.relationship_type
            )
            def fix_edge(edge):
                if len(edge) == 2:
                    edge.append({})
                return edge
            session.run(query, {"edges": [fix_edge(list(edge)) for edge in edges]})


    def update(self, edges=None, nodes=None, graph_id_props=None):
        if edges is not None:
            if nodes is not None:
                self.add_nodes_from(edges)
                self.add_edges_from(nodes)
            else:
                try:
                    graph_nodes = edges.nodes
                    graph_edges = edges.edges
                except:
                    self.add_edges_from(edges)
                else:
                    graph_nodes_data = graph_nodes(data=True)
                    graph_edges_data = graph_edges(data=True)
                    adding_edges = []
                    for u, v, data in graph_edges_data:
                        try:
                            if self.identifier_property in graph_nodes[u]:
                                u = graph_nodes[u][self.identifier_property]
                        except:
                            pass
                        try:
                            if self.identifier_property in graph_nodes[v]:
                                v = graph_nodes[v][self.identifier_property]
                        except:
                            pass
                        adding_edges.append((u, v, data))
                    graph_nodes_data = graph_nodes(data=True)
                    graph_nodes_fixed_data = []
                    for n, d in graph_nodes_data:
                        if graph_id_props is not None:
                            if isinstance(graph_id_props, tuple) or isinstance(graph_id_props, list):
                                for value, v in zip(n, graph_id_props):
                                    d[v] = value
                            else:
                                d[graph_id_props] = n
                        graph_nodes_fixed_data.append((n, d))
                    self.add_nodes_from(graph_nodes_fixed_data)
                    self.add_edges_from(adding_edges)

    _clear_graph_nodes_query = """\
    MATCH (n:`%s`)
    DELETE n
    """

    _clear_graph_edges_query = """\
    MATCH (:`%s`)-[r:`%s`]-(:`%s`)
    DELETE r
    """

    def clear(self):
        with self.driver.session() as session:
            if self.relationship_type:
                query = self._clear_graph_edges_query % (
                    self.node_label,
                    self.relationship_type,
                    self.node_label
                )
                session.run(query)
            query = self._clear_graph_nodes_query % (self.node_label)
            session.run(query)

    number_of_nodes_query = """\
    MATCH (:`%s`)
    RETURN count(*) AS numberOfNodes
    """

    def number_of_nodes(self):
        with self.driver.session() as session:
            query = self.number_of_nodes_query % self.node_label
            return session.run(query).peek()["numberOfNodes"]

    betweenness_centrality_query = """\
    CALL algo.betweenness.stream({nodeLabel}, {relationshipType}, {
        direction: {direction},
        graph: {graph}
    })
    YIELD nodeId, centrality
    MATCH (n) WHERE id(n) = nodeId
    RETURN n.`%s` AS node, centrality
    """

    def betweenness_centrality(self):
        with self.driver.session() as session:
            query = self.betweenness_centrality_query % self.identifier_property
            params = self.base_params()
            result = {row["node"]: row["centrality"] for row in session.run(query, params)}
        return result

    closeness_centrality_query = """\
    CALL algo.closeness.stream({nodeLabel}, {relationshipType}, {
      direction: {direction},
      improved: {wfImproved},
      graph: {graph}
    })
    YIELD nodeId, centrality
    MATCH (n) WHERE id(n) = nodeId
    RETURN n.`%s` AS node, centrality
    """

    def closeness_centrality(self, wf_improved=True):
        with self.driver.session() as session:
            params = self.base_params()
            params["wfImproved"] = wf_improved
            query = self.closeness_centrality_query % self.identifier_property

            result = {row["node"]: row["centrality"] for row in session.run(query, params)}
        return result

    harmonic_centrality_query = """\
    CALL algo.closeness.harmonic.stream({nodeLabel}, {relationshipType}, {
      direction: {direction},
      graph: {graph}
    })
    YIELD nodeId, centrality
    MATCH (n) WHERE id(n) = nodeId
    RETURN n.`%s` AS node, centrality
    """

    def harmonic_centrality(self):
        with self.driver.session() as session:
            params = self.base_params()
            query = self.harmonic_centrality_query % self.identifier_property
            result = {row["node"]: row["centrality"] for row in session.run(query, params)}
        return result

    pagerank_query = """\
    CALL algo.pageRank.stream({nodeLabel}, {relationshipType}, {
      direction: {direction},
      graph: {graph},
      iterations: {iterations},
      dampingFactor: {dampingFactor}
    })
    YIELD nodeId, score
    MATCH (n) WHERE id(n) = nodeId
    RETURN n.`%s` AS node, score
    """

    def pagerank(self, alpha, max_iter):
        with self.driver.session() as session:
            params = self.base_params()
            params["iterations"] = max_iter
            params["dampingFactor"] = alpha

            query = self.pagerank_query % self.identifier_property
            result = {row["node"]: row["score"] for row in session.run(query, params)}
        return result

    triangle_count_query = """\
    CALL algo.triangleCount.stream({nodeLabel}, {relationshipType}, {
      direction: {direction},
      graph: {graph}
    })
    YIELD nodeId, triangles, coefficient
    MATCH (n) WHERE id(n) = nodeId
    RETURN n.`%s` AS node, triangles, coefficient
    """

    def triangles(self):
        with self.driver.session() as session:
            params = self.base_params()
            query = self.triangle_count_query % self.identifier_property
            result = {row["node"]: row["triangles"] for row in session.run(query, params)}
        return result

    def clustering(self):
        with self.driver.session() as session:
            params = self.base_params()
            query = self.triangle_count_query % self.identifier_property
            result = {row["node"]: row["coefficient"] for row in session.run(query, params)}
        return result

    triangle_query = """\
    CALL algo.triangleCount({nodeLabel}, {relationshipType}, {
      direction: {direction},
      graph: {graph},
      write: false
    })
    """

    def average_clustering(self):
        with self.driver.session() as session:
            params = self.base_params()
            query = self.triangle_query
            result = session.run(query, params)
            return result.peek()["averageClusteringCoefficient"]

    lpa_query = """\
    CALL algo.labelPropagation.stream({nodeLabel}, {relationshipType}, {
      direction: {direction},
      graph: {graph}
    })
    YIELD nodeId, label
    MATCH (n) WHERE id(n) = nodeId
    RETURN label, collect(n.`%s`) AS nodes
    """

    def label_propagation(self):
        with self.driver.session() as session:
            params = self.base_params()
            query = self.lpa_query % self.identifier_property

            for row in session.run(query, params):
                yield set(row["nodes"])

    shortest_path_query = """\
    MATCH (source:`%s` {`%s`: {source} })
    MATCH (target:`%s` {`%s`: {target} })
    CALL algo.shortestPath.stream(source, target, {propertyName}, {
      direction: {direction},
      graph: {graph}
    })
    YIELD nodeId, cost
    MATCH (n) WHERE id(n) = nodeId
    RETURN n.`%s` AS node, cost
    """

    def shortest_weighted_path(self, source, target, weight):
        with self.driver.session() as session:
            params = self.base_params()
            params["source"] = source
            params["target"] = target
            params["propertyName"] = weight

            query = self.shortest_path_query % (
                self.node_label,
                self.identifier_property,
                self.node_label,
                self.identifier_property,
                self.identifier_property
            )

            result = [row["node"] for row in session.run(query, params)]
        return result

    def shortest_path(self, source, target):
        with self.driver.session() as session:
            params = self.base_params()
            params["source"] = source
            params["target"] = target
            params["propertyName"] = None

            query = self.shortest_path_query % (
                self.node_label,
                self.identifier_property,
                self.node_label,
                self.identifier_property,
                self.identifier_property
            )

            result = [row["node"] for row in session.run(query, params)]
        return result

    connected_components_query = """\
    CALL algo.unionFind.stream({nodeLabel}, {relationshipType}, {
      direction: {direction},
      graph: {graph}
    })
    YIELD nodeId, setId
    MATCH (n) WHERE id(n) = nodeId
    RETURN setId, collect(n.`%s`) AS nodes
    """

    def connected_components(self):
        with self.driver.session() as session:
            params = self.base_params()
            query = self.lpa_query % self.identifier_property

            for row in session.run(query, params):
                yield set(row["nodes"])

    def base_params(self):
        return {
            "direction": self.direction,
            "nodeLabel": self.node_label,
            "relationshipType": self.relationship_type,
            "graph": self.graph
        }
