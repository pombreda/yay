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

from yay.nodes import Node, BoxingFactory, Sequence
from yay.errors import NoMatching


class Extend(Node):

    """
    Appends an iterable to a sequence

    This gets added to the graph when the parser encounters an ``append`` function::

        example.append:
          - foo
          - bar

    If ``example`` hasn't been previously defined it behaves as if it is append
    to an empty sequence.
    """

    def __init__(self, value):
        super(Extend, self).__init__()
        self.value = value
        value.set_parent(self)

    def get(self, idx, default=None):
        return BoxingFactory.box(self.resolve()[int(idx)])

    def expand(self):
        if not self.predecessor:
            return self.value.expand()

        try:
            predecessor = self.predecessor.expand()
        except NoMatching:
            return self.value.expand()

        if not hasattr(predecessor, "__iter__"):
            self.error("You can only append to list types")

        value = self.value.expand()
        if not hasattr(value, "__iter__"):
            self.error("You must append a list to this field")

        # we initialize this sequence weirdly as we dont want to reparent the nodes we are appending
        s = Sequence([])
        s.value = list(iter(predecessor)) + list(iter(value))
        s.set_parent(self.parent)
        return s

    def resolve(self):
        return self.expand().resolve()
