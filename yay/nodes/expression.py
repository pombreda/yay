# Copyright 2010-2011 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from yay.nodes import Node, Boxed
from yay.protectedstring import ProtectedString


class Comparison(Node):
    def __init__(self, left, right):
        self.left = left
        left.set_parent(self)
        self.right = right
        right.set_parent(self)

    def __repr__(self):
        return "%s(%s, %s)" % (self.__class__.__name__, self.left, self.right)

    def walk(self):
        yield self.left
        yield self.right

    def clone(self):
        return self.__class__(self.left.clone(), self.right.clone())

class And(Comparison):
    def resolve(self):
        return self.left.resolve() and self.right.resolve()

class Or(Comparison):
    def resolve(self):
        return self.left.resolve() or self.right.resolve()

class In(Comparison):
    def resolve(self):
        return self.left.resolve() in self.right.resolve()

class Equal(Comparison):
    def resolve(self):
        return self.left.resolve() == self.right.resolve()

class NotEqual(Comparison):
    def resolve(self):
        return self.left.resolve() != self.right.resolve()

class LessThan(Comparison):
    def resolve(self):
        return self.left.resolve() < self.right.resolve()

class LessThanEqual(Comparison):
    def resolve(self,):
        return self.left.resolve() <= self.right.resolve()

class GreaterThan(Comparison):
    def resolve(self):
        return self.left.resolve() > self.right.resolve()

class GreaterThanEqual(Comparison):
    def resolve(self):
        return self.left.resolve() >= self.right.resolve()


class Access(Node):
    def __init__(self, container, access):
        self.container = container
        if container:
            container.set_parent(self)
        self.access = access
        self.access.set_parent(self)

    def get(self, idx):
        sr = self.expand()
        return sr.get(idx)

    def expand(self):
        key = self.access.resolve()

        if self.container:
            unresolved = self.container.get(key)
            if unresolved is None:
                self.error("Container does not have field '%s'" % key)
        else:
            unresolved = self.get_context(key)
            if unresolved is None:
                self.error("Context does not have field '%s'" % key)

        if hasattr(unresolved, "expand"):
            return unresolved.expand()

        return unresolved

    def resolve(self):
        sr = self.expand()
        return sr.resolve()

    def walk(self):
        yield self.expand()

    def __repr__(self):
        return "Access(%s, %s)" % (self.container, self.access)

    def clone(self):
        c = None
        if self.container:
            c = self.container.clone()
        return Access(c, self.access.clone())


class Concatenation(Node):
    def __init__(self, *args):
        self.args = args
        [x.set_parent(self) for x in args]

    def resolve(self):
        resolved = [x.resolve() for x in self.args]

        protected = False
        for x in resolved:
            if isinstance(x, ProtectedString):
                protected = True

        if protected:
            p = ProtectedString()
            for x in resolved:
                p.add(x)
            return p

        return "".join(str(x) for x in resolved)

    def walk(self):
        for arg in self.args:
            yield arg

    def __repr__(self):
        return "Concat(%s)" % ", ".join(str(arg) for arg in self.args)

    def clone(self):
        return Concatenation(*[x.clone() for x in self.args])

