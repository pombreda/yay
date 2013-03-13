import operator
from . import errors
from .openers import Openers


class AST(object):

    lineno = 0
    predecessor = None

    def as_int(self, anchor=None):
        raise errors.TypeError("Expected integer", anchor=anchor or self.anchor)

    def as_float(self, anchor=None):
        raise errors.TypeError("Expected float", anchor=anchor or self.anchor)

    def as_number(self, anchor=None):
        raise errors.TypeError("Expected integer or float", anchor=anchor or self.anchor)

    def as_safe_string(self, anchor=None):
        raise errors.TypeError("Expected string", anchor=anchor or self.anchor)

    def as_string(self, anchor=None):
        raise errors.TypeError("Expected string", anchor=anchor or self.anchor)

    def as_iterable(self, anchor=None):
        raise errors.TypeError("Expected iterable", anchor=self.anchor)

    def dynamic(self):
        """
        Does this graph member change over time?
        """
        return False

    def simplify(self):
        """
        Resolve any parts of the graph that are constant
        """
        return self

    def resolve(self):
        """
        Resolve an object into a simple type, like a string or a dictionary.

        Node does not provide an implementation of this, all subclasses should
        implemented it.
        """
        raise NotImplementedError(self.resolve)

    def expand(self):
        """
        Generate a simplification of this object that can replace it in the graph
        """
        return self

    def get_context(self, key):
        """
        Look up value of ``key`` and return it.

        This doesn't do any resolving, the return value will be a subclass of Node.
        """
        return self.parent.get_context(key)

    def get_root(self):
        """
        Find and return the root of this document.
        """
        return self.parent.get_root()

    def error(self, exc):
        raise ValueError("Runtime errors deliberately nerfed for PoC")

    def clone(self):
        """
        Return a copy of this node.

        This boldly assumes the graph is acyclic.
        """
        def _clone(v):
            if isinstance(v, AST):
                child = v.clone()
                child.parent = instance
                return child
            elif isinstance(v, list):
                lst = []
                for child in v:
                    lst.append(_clone(child))
                return lst
            elif isinstance(v, dict):
                dct = {}
                for k, child in v.items():
                    dct[k] = _clone(child)
                return dct
            else:
                return v

        instance = self.__class__.__new__(self.__class__)
        for k, v in self.__clone_vars().items():
            instance.__dict__[k] = _clone(v)

        return instance

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.__repr_vars())

    def __clone_vars(self):
        d = self.__dict__.copy()
        for var in ('parent', 'predecessor'):
            if var in d:
                del d[var]
        return d

    def __repr_vars(self):
        d = self.__dict__.copy()
        for var in ('anchor', 'parent', 'predecessor'):
            if var in d:
                del d[var]
        return d

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__repr_vars() == other.__repr_vars()


class Scalarish(object):

    """
    A mixin for an object that is a number, string or boolean

    By default if a casting error occurs an errors.ValueError will be raised
    that blames the current node. By passing in the optional ``anchor`` node
    you can blame the node that is consuming this node. For example::

        a: foo
        b: 5
        c: {{ a - b }}

    The most useful error here is to blame the identifier ``a`` inside the
    ``{{ brackets }}`` rather than to actually blame the scalar itself.

    A scalar cannot be treated as a stream.
    """

    def as_int(self, anchor=None):
        try:
            return int(self.resolve())
        except ValueError:
            raise errors.TypeError("Expected integer", anchor=anchor or self.anchor)

    def as_float(self, anchor=None):
        try:
            return float(self.resolve())
        except ValueError:
            raise errors.TypeError("Expected float", anchor=anchor or self.anchor)

    def as_number(self, anchor=None):
        """
        This will return an integer, and if it can't return an integer it
        will return a float. Otherwise it will fail with a TypeError.
        """
        resolved = self.resolve()
        try:
            return int(resolved)
        except ValueError:
            try:
                return float(resolved)
            except ValueError:
                raise errors.TypeError("Expected integer or float", anchor=anchor or self.anchor)

    def as_safe_string(self, anchor=None):
        """ Returns a string that might includes obfuscation where secrets are used """
        return self.as_string(anchor)

    def as_string(self, anchor=None):
        resolved = self.resolve()
        if isinstance(resolved, (int, float, bool)):
            resolved = str(resolved)
        if not isinstance(resolved, basestring):
            raise errors.TypeError("Expected string", anchor=anchor or self.anchor)
        return resolved

class Streamish(object):
    """
    A mixin for a class that behaves like a stream - i.e. is iterable
    """

    def __init__(self):
        self._buffer = []
        self._iterator = None

    def _fill_to(self, index):
        if not self._iterator:
            self._iterator = self.as_iterable()

        while len(self._buffer) < index+1:
            self._buffer.append(self._iterator.next())

    def get_index(self, index):
        self._fill_to(index)
        return self._buffer[index]

    def resolve(self):
        return list(flatten(x.resolve() for x in self.as_iterable()))

class Proxy(object):
    """
    A mixin that forwards requested on to an expanded form
    """

    def as_int(self, anchor=None):
        return self.expand().as_int(anchor or self.anchor)

    def as_float(self, anchor=None):
        return self.expand().as_float(anchor or self.anchor)

    def as_number(self, anchor=None):
        return self.expand().as_number(anchor or self.anchor)

    def as_safe_string(self, anchor=None):
        return self.expand().as_safe_string(anchor or self.anchor)

    def as_string(self, anchor=None):
        return self.expand().as_string(anchor or self.anchor)

    def as_iterable(self, anchor=None):
        return self.expand().as_iterable(anchor or self.anchor)

class Root(AST):
    """ The root of the document
    FIXME: This needs thinking about some more
    """
    def __init__(self, node):
        self.openers = Openers(searchpath=[])
        self.node = node
        node.parent = self

    def get_root(self):
        return self

    def get_callable(self, key):
        p = self.node
        while p:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get_context(self, key):
        return self.node.get(key)

    def resolve(self):
        return self.node.resolve()

    def parse(self, path):
        stream = self.openers.open(path)
        from yay import parser
        return parser.parse(stream.read())

class Identifier(Proxy, AST):
    def __init__(self, identifier):
        self.identifier = identifier

    def expand(self):
        return self.get_context(self.identifier).expand()

    def resolve(self):
        return self.expand().resolve()

class Literal(Scalarish, AST):
    def __init__(self, literal):
        self.literal = literal
    def resolve(self):
        return self.literal

class ParentForm(Scalarish, AST):
    # FIXME: Understand this better...
    def __init__(self, expression_list=None):
        self.expression_list = expression_list
        if expression_list:
            expression_list.parent = self
    def resolve(self):
        if not self.expression_list:
            return []
        return self.expression_list.resolve()

class ExpressionList(AST):
    def __init__(self, *expressions):
        self.expression_list = list(expressions)
        for expr in self.expression_list:
            expr.parent = self

    def append(self, expression):
        self.expression_list.append(expression)

    def resolve(self):
        return [expr.resolve() for expr in self.expression_list]

class Power(AST):
    def __init__(self, primary, power=None):
        self.primary = primary
        primary.parent = self
        self.power = power
        power.parent = self

    def resolve(self):
        return pow(self.primary.as_number(), self.power.as_number())

class UnaryMinus(AST):
    """ The unary - (minus) operator yields the negation of its numeric
    argument. """

    def __init__(self, u_expr):
        self.u_expr = u_expr
        u_expr.parent = self

    def resolve(self):
        return -self.u_expr.as_number()

class Invert(AST):
    """ The unary ~ (invert) operator yields the bitwise inversion of its
    plain or long integer argument. The bitwise inversion of x is defined as
    -(x+1). It only applies to integral numbers. """
    def __init__(self, u_expr):
        self.u_expr = u_expr
        u_expr.parent = self

    def resolve(self):
        return ~self.u_expr.as_number()

class Expr(Scalarish, AST):

    """
    The ``Expr`` node tests for equality between a left and a right child. The
    result is either True or False.

    Tree reduction rules
    --------------------

    If both children are constant then this node can be reduced to a
    ``Literal``

    Otherwise, an equivalent ``Expr`` node is returned that has had its children
    simplified.
    """

    operators = {
        "==": operator.eq,
        "!=": operator.ne,
        "<": operator.lt,
        ">": operator.gt,
        "<=": operator.le,
        ">=": operator.ge,
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.div,
        "or": operator.or_,
        "and": operator.and_,
        "not in": lambda x, y: not x in y,
    }

    def __init__(self, lhs, rhs, operator):
        self.lhs = lhs
        lhs.parent = self
        self.rhs = rhs
        rhs.parent = self
        self.operator = operator
        self.op = self.operators[operator]

    def resolve(self):
        l = self.lhs.resolve()
        r = self.rhs.resolve()
        return self.op(l, r)

    def dynamic(self):
        for c in (self.lhs, self.rhs):
            if c.dynamic():
                return True
        return False

    def simplify(self):
        # FIXME: Would be kind of nice if parser could directly spawn And nodes, i guess...
        # (And and Or can be more agressively simplified than the others)
        if self.operator == "and":
            return And(self.lhs.simplify(), self.rhs.simplify()).simplify()
        elif self.operator == "or":
            return Or(self.lhs.simplify(), self.rhs.simplify()).simplify()
        elif not self.dynamic():
            return Literal(self.op(self.lhs.resolve(), self.rhs.resolve()))
        else:
            return Expr(self.lhs.simplify(), self.rhs.simplify(), self.operator)

    def resolve(self):
        # FIXME: This is horrible and requires more thought
        if self.operator == "or":
            try:
                res = self.lhs.resolve()
                if res:
                    return res
            except errors.NoMatching:
                pass
            return self.rhs.resolve()
        elif self.operator in ("==", "!="):
            return self.op(self.lhs.resolve(), self.rhs.resolve())
        elif self.operator == "+":
            try:
                return self.op(self.lhs.as_number(), self.rhs.as_number())
            except errors.TypeError:
                return self.op(self.lhs.as_string(), self.rhs.as_string())
        else:
            return self.op(self.lhs.as_number(), self.rhs.as_number())


class And(AST):

    """
    An ``And`` expression behaves much like the ``and`` keyword in python.

    Tree reduction rules
    --------------------

    If both parts of the expression are constant then the expression can be
    reduced to a Literal.

    If only one part is constant then it is tested to see if it is False.
    If so, the entire expression is simplified to ``Literal(False)``. If it is
    ``True`` then the ``And`` expression is reduced to the dynamic part of the
    expression.

    If both parts are dynamic then the And cannot be reduced. (However, a new
    And is returned that has its contents reduced).
    """

    def __init__(self, left, right):
        self.left = left
        self.left.parent = self
        self.right = right
        self.right.parent = self

    def dynamic(self):
        for c in (self.left, self.right):
            if c.dynamic():
                return True
        return False

    def simplify(self):
        if self.left.dynamic():
            if self.right.dynamic():
                return And(self.left.simplify(), self.right.simplify())
            elif self.right.resolve():
                return self.left.simplify()
            else:
                return Literal(False)

        elif self.right.dynamic():
            if self.left.resolve():
                return self.right.simplify()
            else:
                return Literal(False)

        return Literal(self.left.resolve() and self.right.resolve())

    def resolve(self):
        return self.left.resolve() and self.right.resolve()


class Not(AST):
    def __init__(self, value):
        self.value = value
        value.parent = self

    def resolve(self):
        return not self.value.resolve()

class ConditionalExpression(AST):
    def __init__(self, or_test, if_clause, else_clause):
        self.or_test = or_test
        self.if_clause = if_clause
        self.else_clause = else_clause
    def resolve(self):
        if self.or_test.resolve():
            return self.if_clause.resolve()
        else:
            return self.else_clause.resolve()

class ListDisplay(AST):
    def __init__(self, expression_list=None):
        self.expression_list = expression_list

    def resolve(self):
        if not self.expression_list:
            return []

class DictDisplay(AST):

    def __init__(self, key_datum_list=None):
        self.key_datum_list = key_datum_list

    def resolve(self):
        if not self.key_datum_list:
            return {}

class KeyDatumList(AST):

    def __init__(self, *key_data):
        self.key_data = list(key_data)

    def append(self, key_datum):
        self.key_data.append(key_datum)

class KeyDatum(AST):

    def __init__(self, key, value):
        self.key = key
        self.value = value

class AttributeRef(Proxy, AST):
    def __init__(self, primary, identifier):
        self.primary = primary
        primary.parent = self
        self.identifier = identifier

    def expand(self):
        return self.primary.expand().get(self.identifier).expand()

    def resolve(self):
        return self.expand().resolve()

class LazyPredecessor(Proxy, AST):
    def __init__(self, node, identifier):
        # This is a sideways reference! No parenting...
        self.node = node
        self.identifier = identifier

    @property
    def anchor(self):
        return self.expand().anchor

    def get(self, key):
        predecessor = self.expand()
        if not predecessor:
            raise errors.NoMatching("No such key '%s'" % key)
        return predecessor.get(key)

    def expand(self):
        if not self.node.predecessor:
            raise errors.NoPredecessor
        return self.node.predecessor.expand().get(self.identifier)

    def resolve(self):
        return self.expand().resolve()

class UseMyPredecessorStandin(AST):
    def __init__(self, node):
        # This is a sideways reference! No parenting...
        self.node = node

    def get(self, key):
        predecessor = self.expand()
        if not predecessor:
            raise errors.NoMatching("No such key '%s'" % key)
        return predecessor.get(key)

    def expand(self):
        if not self.node.predecessor:
            raise errors.NoPredecessor
        return self.node.predecessor.expand()

    def resolve(self):
        return self.expand().resolve()

class Subscription(Proxy, AST):
    def __init__(self, primary, *expression_list):
        self.primary = primary
        primary.parent = self
        self.expression_list = list(expression_list)
        if len(self.expression_list) > 1:
            self.error("Keys must be scalars, not tuples")
        for e in self.expression_list:
            e.parent = self

    def expand(self):
        return self.primary.expand().get(self.expression_list[0].resolve()).expand()

    def resolve(self):
        return self.expand().resolve()

class SimpleSlicing(Streamish, AST):
    def __init__(self, primary, short_slice):
        super(SimpleSlicing, self).__init__()
        self.primary = primary
        primary.parent = self
        self.short_slice = short_slice
        short_slice.parent = self

    def as_iterable(self):
        lower_bound = self.short_slice.lower_bound.resolve()
        upper_bound = self.short_slice.upper_bound.resolve()
        stride = self.short_slice.stride.resolve()

        for i in range(lower_bound, upper_bound, stride):
            yield self.primary.expand().get_index(i)

class ExtendedSlicing(Streamish, AST):
    def __init__(self, primary, slice_list):
        self.primary = primary
        primary.parent = self
        self.slice_list = slice_list
        slice_list.parent = self

    def as_iterable(self):
        short_slice = self.slice_list.slice_list[0]

        lower_bound = short_slice.lower_bound.resolve()
        upper_bound = short_slice.upper_bound.resolve()
        stride = short_slice.stride.resolve()

        for i in range(lower_bound, upper_bound, stride):
            yield self.primary.expand().get_index(i)

class SliceList(AST):
    def __init__(self, slice_item):
        self.slice_list = [slice_item]

    def append(self, slice_item):
        self.slice_list.append(slice_item)

class Slice(AST):
    def __init__(self, lower_bound=None, upper_bound=None, stride=None):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.stride = stride or YayScalar(1)


import re

class Call(Proxy, AST):

    allowed = {
        "range": range,
        "replace": lambda i, r, w: i.replace(r, w),
        "sub": re.sub,
        }

    def __init__(self, primary, args=None, kwargs=None):
        self.primary = primary
        self.args = args
        if self.args:
            for arg in self.args:
                arg.parent = self
        self.kwargs = kwargs

    def expand(self):
        kwargs = {}
        for kwarg in self.kwargs.kwargs:
            k = kwargs[kwarg.identifier.identifier] = kwarg.expression.clone()

        call = CallDirective(self.primary, None)
        call.anchor = self.anchor
        context = Context(call, kwargs)
        context.parent = self
        return context.expand()

    def resolve(self):
        if self.args:
            args = [x.resolve() for x in self.args]
        else:
            args = []
        try:
            return self.allowed[self.primary.identifier](*args)
        except KeyError:
            pass


class ArgumentList(AST):
    def __init__(self, args, kwargs=None):
        self.args = args
        self.kwargs = kwargs

class PositionalArguments(AST):
    def __init__(self, *expressions):
        self.args = list(expressions)

    def append(self, expression):
        self.args.append(expression)

class KeywordArguments(AST):
    def __init__(self, *keyword_items):
        self.kwargs = list(keyword_items)

    def append(self, keyword_item):
        self.kwargs.append(keyword_item)

class Kwarg(AST):
    def __init__(self, identifier, expression):
        self.identifier = identifier
        self.expression = expression

class TargetList(AST):
    def __init__(self, *targets):
        self.v = list(targets)

    def append(self, target):
        self.v.append(target)

class ParameterList(AST):
    def __init__(self, defparameter):
        self.parameter_list = [defparameter]

    def append(self, defparameter):
        self.parameter_list.append(defparameter)

class DefParameter(AST):
    def __init__(self, parameter, expression=None):
        self.parameter = parameter
        self.expression = expression

class Sublist(AST):
    def __init__(self, parameter):
        self.sublist = [parameter]

    def append(self, parameter):
        self.sublist.append(parameter)

class YayList(AST):
    def __init__(self, *items):
        self.value = list(items)
        for x in self.value:
            x.parent = self

    def append(self, item):
        self.value.append(item)
        item.parent = self

    def resolve(self):
        l = []
        for i in self.value:
            l.append(i.resolve())
        return l

    def get(self, idx):
        return self.get_index(idx)

    def get_index(self, idx):
        try:
            idx = int(idx)
        except ValueError:
            self.error("Expected integer but got '%s'" % idx)

        if idx < 0:
            self.error("Index must be greater than 0")
        elif idx >= len(self.value):
            self.error("Index out of range")

        return self.value[idx]

    def as_iterable(self, anchor=None):
        return iter(self.value)

class YayDict(AST):

    """ A dictionary in yay may redefine items, so update merely appends. The
    value is a list of 2-tuples """

    def __init__(self, value=None):
        self.values = {}
        if value:
            for (k, v) in value:
                self.update(k, v)

    def update(self, k, v):
        try:
            predecessor = self.get(k)
        except errors.NoMatching:
            predecessor = LazyPredecessor(self, k)

        v.parent = self
        self.values[k] = v

        # Respect any existing predecessors rather than blindly settings v.predecessor
        while v.predecessor and not isinstance(v.predecessor, LazyPredecessor):
            v = v.predecessor
            v.parent = self
        v.predecessor = predecessor

    def merge(self, other_dict):
        # This function should ONLY be called by parser and ONLY to merge 2 YayDict nodes...
        assert isinstance(other_dict, YayDict)
        for k, v in other_dict.values.items():
            self.update(k, v)

    def keys(self):
        keys = set(self.values.keys())
        try:
            expanded = self.predecessor.expand()
            if not hasattr(expanded, "keys"):
                self.error("Mapping cannot mask or replace field with same name and different type")
            keys.update(expanded.keys())
        except errors.NoPredecessor:
            pass
        return sorted(list(keys))

    def get(self, key):
        if key in self.values:
            return self.values[key]
        if not self.predecessor:
            #FIXME: I would dearly love to get rid of this check and have every node have a LazyPredecessor
            raise errors.NoMatching("No such key '%s'" % key)
        try:
            return self.predecessor.expand().get(key)
        except errors.NoPredecessor:
            raise errors.NoMatching("Key '%s' not found" % key)

    def as_iterable(self, anchor=None):
        for k in self.keys():
            yield YayScalar(k)

    def resolve(self):
        d = {}
        try:
            if self.predecessor:
                d = self.predecessor.resolve()
        except errors.NoPredecessor:
            d = {}

        for k, v in self.values.items():
            d[k] = v.resolve()

        return d

class YayExtend(Streamish, AST):
    def __init__(self, value):
        self.value = value
        value.parent = self

    def as_iterable(self, anchor=None):
        if self.predecessor:
            try:
                for node in self.predecessor.as_iterable(anchor or self.anchor):
                    yield node
            except errors.NoPredecessor:
                pass

        for node in self.value.as_iterable(anchor or self.anchor):
            yield node


class YayScalar(Scalarish, AST):
    def __init__(self, value):
        try:
            self.value = int(value)
        except ValueError:
            try:
                self.value = float(value)
            except ValueError:
                self.value = value

    def resolve(self):
        return self.value

class YayMerged(AST):
    """ Combined scalars and templates """

    def __init__(self, *v):
        self.value = list(v)
        for v in self.value:
            v.parent = self

    def append(self, v):
        self.value.append(v)
        v.parent = self

    def prepend(self, value):
        self.value.insert(0, value)
        value.parent = self

    def resolve(self):
        return "".join(str(v.resolve()) for v in self.value)

class Stanzas(AST):
    def __init__(self, *stanzas):
        self.value = UseMyPredecessorStandin(self)
        for s in stanzas:
            self.append(s)

    def append(self, stanza):
        stanza.predecessor = self.value
        stanza.parent = self
        self.value = stanza

    def get_callable(self, key):
        p = self.value
        while p and p != self.predecessor:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get(self, key):
        return self.value.get(key)

    def resolve(self):
        return self.value.resolve()

class Directives(AST):
    def __init__(self, *directives):
        self.value = None
        for d in directives:
            self.append(d)

    def append(self, directive):
        directive.parent = self
        directive.predecessor = self.value
        self.value = directive

    def get_callable(self, key):
        p = self.value
        while p and p != self.predecessor:
            if hasattr(p, "get_callable"):
                try:
                    return p.get_callable(key)
                except errors.NoMatching:
                    pass
            p = p.predecessor
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get(self, key):
        return self.value.get(key)

    def expand(self):
        return self.value.expand()

    def resolve(self):
        return self.value.resolve()

class Include(AST):

    def __init__(self, expr):
        self.expr = expr
        expr.parent = self
        self.detector = []

    def get_callable(self, key):
        expanded = self.expand()
        if hasattr(expanded, "get_callable"):
            return expanded.get_callable(key)
        raise errors.NoMatching("Could not find a macro called 'SomeMacro'")

    def get(self, key):
        if key in self.detector:
            raise errors.NoMatching("'%s' not found" % key)
        try:
            self.detector.append(key)
            return self.expand().get(key)
        finally:
            self.detector.remove(key)

    def expand(self):
        expanded = self.get_root().parse(self.expr.resolve())
        expanded.predecessor = self.predecessor
        expanded.parent = self.parent
        return expanded

    def resolve(self):
        return self.expand().resolve()

class Search(AST):

    def __init__(self, expr):
        self.expr = expr

class Configure(AST):

    def __init__(self, key, node):
        self.key = key
        self.node = node

class Set(AST):

    def __init__(self, var, expr):
        self.var = var
        self.expr = expr

    def __repr__(self):
        return "<Set %r = %r>" % (self.var, self.expr)


class If(AST):
    # FIXME: This implementation ignores the elifs...

    """
    An If block has a guard condition. If that condition is True the
    result expression is returned. Otherwise the else_ expression is.

    Tree reduction rules
    --------------------

    If the guard condition is constant then the If expression can be
    simplified out of the graph.
    """

    def __init__(self, condition, result, elifs=None, else_=None):
        self.condition = condition
        condition.parent = self
        self.result = result
        result.parent = self
        self.elifs = elifs
        if elifs:
            elifs.parent = self
        self.else_ = else_
        if else_:
            else_.parent = self
        self.passthrough_mode = False

    def dynamic(self):
        if self.condition.dynamic():
            return True
        if self.condition.resolve():
            if self.result.dynamic():
                return True
        else:
            if self.else_.dynamic():
                return True
        return False

    def simplify(self):
        if self.condition.dynamic():
            return If(self.condition.simplify(), self.result.simplify(), else_=self.else_.simplify())
        if self.condition.resolve():
            return self.result.simplify()
        else:
            return self.else_.simplify()

    def get(self, key):
        if self.passthrough_mode:
            return self.predecessor.get(key)

        self.passthrough_mode = True
        cond = self.condition.resolve()
        self.passthrough_mode = False

        try:
            if cond:
                return self.result.get(key)

            if self.elifs:
                for elif_ in self.elifs.elifs:
                    self.passthrough_mode = True
                    cond = elif_.condition.resolve()
                    self.passthrough_mode = False
                    if cond:
                        return elif_.node.get(key)

            if self.else_ is not None:
                return self.else_.get(key)

            return self.predecessor.get(key)

        except errors.NoMatching:
            return self.predecessor.get(key)

    def resolve(self):
        if self.condition.resolve():
            return self.result.resolve()

        if self.elifs:
            for elif_ in self.elifs.elifs:
                if elif_.condition.resolve():
                    return elif_.node.resolve()

        if self.else_ is not None:
            return self.else_.resolve()

        return self.predecessor.resolve()


class ElifList(AST):
    def __init__(self, *elifs):
        self.elifs = []
        [self.append(e) for e in elifs]

    def append(self, elif_):
        elif_.parent = self
        self.elifs.append(elif_)

class Elif(AST):
    def __init__(self, condition, node):
        self.condition = condition
        condition.parent = self
        self.node = node
        node.parent = self

class Select(AST):

    def __init__(self, expr, cases):
        self.expr = expr
        self.cases = cases

class CaseList(object):
    def __init__(self, *cases):
        self.cases = list(cases)

    def append(self, case):
        self.cases.append(case)

class Case(object):
    def __init__(self, key, node):
        self.key = key
        self.node = node


def flatten(lst):
    for itm in lst:
        if isinstance(itm, list):
            for x in flatten(itm):
                yield x
        else:
            yield itm

class Create(AST):
    def __init__(self, target, node):
        self.target = target
        self.node = node

class Macro(AST):
    def __init__(self, target, node):
        self.target = target
        self.node = node

    def get_callable(self, key):
        if key == self.target.identifier:
            return self
        raise errors.NoMatching("Could not find a macro called '%s'" % key)

    def get(self, key):
        if not self.predecessor:
            raise errors.NoPredecessor()
        return self.predecessor.get(key)

    def expand(self):
        if not self.predecessor:
            raise errors.NoPredecessor()
        return self.predecessor.expand()

    def resolve(self):
        if not self.predecessor:
            raise errors.NoPredecessor()
        return self.predecessor.resolve()

class CallDirective(Proxy, AST):
    def __init__(self, target, node):
        self.target = target
        self.node = node

    def expand(self):
        macro = self.get_root().get_callable(self.target.identifier)
        clone = macro.node.clone()
        if not self.node:
            clone.parent = self
            return clone.expand()
        context = Context(clone, self.node.expand().values)
        context.parent = self
        return context.expand()

    def resolve(self):
        return self.expand().resolve()

class For(Streamish, AST):

    def __init__(self, target, in_clause, node, if_clause=None):
        super(For, self).__init__()

        self.target = target
        target.parent = self
        self.if_clause = if_clause
        if if_clause:
            if_clause.parent = self
        self.in_clause = in_clause
        in_clause.parent = self
        self.node = node
        node.parent = self

    def as_iterable(self, anchor=None):
        for item in self.in_clause.as_iterable(anchor):
            # self.target.identifier: This probably shouldn't be an identifier
            c = Context(self.node.clone(), {self.target.identifier: item.clone()})
            c.parent = self.parent

            if self.if_clause:
                f = self.if_clause.clone()
                f.parent = c
                if not f.resolve():
                    continue

            yield c


class Template(Scalarish, AST):
    def __init__(self, *value):
        self.value = list(value)
        for v in self.value:
            v.parent = self

    def as_iterable(self, anchor=None):
        # If template only contains one item it may be iterable - let it try
        # Otherwise defer to Scalarish behaviour
        if len(self.value) == 1:
            return self.value[0].as_iterable()
        super(Template, self).as_iterator(anchor)

    def resolve(self):
        if len(self.value) == 1:
            return self.value[0].resolve()
        return ''.join(str(v.resolve()) for v in self.value)

class Context(Proxy, AST):

    def __init__(self, value, context):
        self.value = value
        self.value.parent = self
        self.context = context

    def get_context(self, key):
        """
        If ``key`` is provided by this node return it, otherwise fall
        back to default implementation.
        """
        val = self.context.get(key, None)
        if not val:
            val = super(Context, self).get_context(key)
        return val

    def expand(self):
        return self.value.expand()

    def resolve(self):
        return self.value.resolve()

class ListComprehension(AST):
    def __init__(self, expression, list_for):
        self.expression = expression
        self.list_for = list_for

class ListFor(AST):
    def __init__(self, targets, expressions, iterator=None):
        self.targets = targets
        self.expressions = expressions
        self.iterator = iterator


class ListIf(AST):
    def __init__(self, expression, iterator=None):
        self.expression = expression
        self.iterator = iterator

class Comprehension(AST):
    def __init__(self, expression, comp_for):
        self.expression = expression
        self.comp_for = comp_for

class CompFor(AST):
    def __init__(self, targets, test, iterator=None):
        self.targets = targets
        self.test = test
        self.iterator = iterator

class CompIf(AST):
    def __init__(self, expression, iterator=None):
        self.expression = expression
        self.iterator = iterator

class GeneratorExpression(AST):
    def __init__(self, expression, comp_for):
        self.expression = expression
        self.comp_for = comp_for

class DictComprehension(AST):
    def __init__(self, key, value, comp_for):
        self.key = key
        self.value = value
        self.comp_for = comp_for

class SetDisplay(AST):
    def __init__(self, v):
        self.v = v

class StringConversion(AST):
    def __init__(self, v):
        self.v = v

class LambdaForm(AST):
    def __init__(self, expression, params=None):
        self.expression = expression
        self.params = params

class Comment(AST):
    def __init__(self, v):
        self.v = v
