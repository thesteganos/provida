class StateGraph:
    def __init__(self, state_cls):
        self.state_cls = state_cls
        self.nodes = {}
        self.entry_point = None

    def add_node(self, name, func):
        self.nodes[name] = func

    def set_entry_point(self, name):
        self.entry_point = name

    def add_edge(self, from_node, to_node):
        pass

    def compile(self):
        func = self.nodes.get(self.entry_point)
        class Workflow:
            def __init__(self, fn):
                self.fn = fn
            def invoke(self, state):
                return self.fn(state)
        return Workflow(func)

END = "END"
