from nxneo4j.base_graph import BaseGraph


class Graph(BaseGraph):
    def __init__(self, driver, config=None):
        BaseGraph.__init__(self, driver, "BOTH", config)
