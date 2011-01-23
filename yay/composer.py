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

from yaml.error import MarkedYAMLError
from yaml.events import ScalarEvent, SequenceStartEvent, SequenceEndEvent, \
    MappingStartEvent, MappingEndEvent, AliasEvent, StreamEndEvent

from yay.nodes import *
from yay.parser import templated_string, as_statement


class ComposerError(MarkedYAMLError):
    pass


class Composer(object):
    """
    I turn the 'parse trees' (repr'd as ordered dictionarys and other
    primitives) into a compile tree
    """

    def __init__(self):
        self.root = None
        self.action_map = {
            "copy": lambda value, args: Copy(value),
            "assign": lambda value, args: value if isinstance(value, Node) else Boxed(value),
            "append": lambda value, args: Append(value),
            "remove": lambda value, args: Remove(value),
            "foreach": lambda value, args: ForEach(self, value, as_statement.parseString(args)),
            }

    def compose(self, previous):
        # Drop the STREAM-START event.
        self.get_event()

        # Compose a document if the stream is not empty.
        document = None
        if not self.check_event(StreamEndEvent):
            self.get_event() # Drop DOCUMENT-START
            document = self.compose_node(previous)
            self.get_event() # Drop DOCUMENT-END

        # Ensure that the stream contains no more documents.
        if not self.check_event(StreamEndEvent):
            event = self.get_event()
            raise ComposerError("expected a single document in the stream",
                    document.start_mark, "but found another document",
                    event.start_mark)

        # Drop the STREAM-END event.
        self.get_event()

        return document

    def compose_node(self, previous):
        if self.check_event(AliasEvent):
            raise ComposerError(None, None, "found alias, these arent supported in yay", event.start_mark)

        node = None

        if self.check_event(ScalarEvent):
            node = self.compose_scalar(previous)
        elif self.check_event(SequenceStartEvent):
            node = self.compose_sequence(previous)
        elif self.check_event(MappingStartEvent):
            node = self.compose_mapping(previous)

        if not node:
            event = self.peek_event()
            raise ComposerError(None, None, "unexpected event in stream", event.start_mark)

        return node

    def compose_scalar(self, previous):
        event = self.get_event()

        if isinstance(event.value, basestring):
            #Icky - this needs to move *beneath* this layer of code
            node = templated_string.parseString(event.value)[0]
        else:
            node = Boxed(event.value)

        node.start_mark = event.start_mark
        node.end_mark = event.end_mark

        return node

    def compose_sequence(self, previous):
        start = self.get_event()

        data = []
        while not self.check_event(SequenceEndEvent):
            data.append(self.compose_node(None))

        end = self.get_event()

        node = Sequence(data)
        node.start_mark = start.start_mark
        node.end_mark = end.end_mark

        return node

    def compose_mapping(self, previous):
        start = self.get_event()

        container = Mapping(previous)
        while not self.check_event(MappingEndEvent):
            key_event = self.get_event()
            key = key_event.value

            action = "assign"
            if "." in key:
                key, action = key.split(".", 1)

            action_args = None
            if " " in action:
                action, action_args = action.split(" ", 1)

            # FIXME: context-driven traversal is different from non-resolving dict-lookup
            existing = container.get(None, key, None)

            # Grab scalar value
            boxed = self.compose_node(existing)

            # Further box the value based on the kind of action it is
            boxed = self.action_map[action](boxed, action_args)

            # Make sure that Appends are hooked up to correct List
            boxed.chain = existing

            # And add it to the dictionary (which will automatically chain nodes)
            container.set(key, boxed)

        end = self.get_event()

        container.start_mark = start.start_mark
        container.end_mark = end.end_mark

        return container


