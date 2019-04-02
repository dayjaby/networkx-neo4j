from nxneo4j.base_graph import BaseGraph


class DiGraph(BaseGraph):
    def __init__(self, driver, config=None):
        BaseGraph.__init__(self, driver, "OUTGOING", config)
