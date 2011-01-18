
from yay.nodes import Node

class Filter(Node):

    def __init__(self, container, filter_expression):
        self.container = container
        self.filter_expression = filter_expression

    def semi_resolve(self, context):
        if not hasattr(self.container, "semi_resolve"):
            raise ValueError("Expected sequence, got '%s'" % self.container)

        resolved = self.container.semi_resolve(context)

        filtered = []
        for r in resolved:
            filtered.append(r)

        return filtered

    def resolve(self, context):
        return list(f.resolve(context) for f in self.semi_resolve(context))

    def __repr__(self):
        return "Filter(%s, %s)" % (self.container, self.filter_expression)