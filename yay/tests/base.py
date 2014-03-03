# Copyright 2012 Isotoma Limited
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

import unittest

try:
    from imp import reload
except:
    pass
import os
import tempfile

from yay.compat import io
from yay import parser, ast, config
from yay.openers.base import MemOpener


class MockRoot(ast.Root):

    def __init__(self, node):
        super(MockRoot, self).__init__(node)
        self.data = {}

    def add(self, key, value):
        self.data[key] = value

    def _parse_uri(self, path):
        p = parser.Parser()
        return p.parse(self.data[path], debug=0)


def bare_parse(value, debug=False):
    try:
        import yay.parsetab
        reload(yay.parsetab)
    except ImportError:
        pass
    p = parser.Parser()
    return p.parse(value, debug)


def parse(value, root=MockRoot, **kwargs):
    r = root(bare_parse(value))
    for k, v in kwargs.items():
        r.add(k, v)
    return r


def resolve(value, root=MockRoot, **kwargs):
    r = parse(value, root, **kwargs)
    return r.resolve()


class TestCase(unittest.TestCase):

    builtins = None

    def setUp(self):
        self.addCleanup(MemOpener.reset)

    def _add(self, key, data):
        MemOpener.add(key, data)

    def _parse(self, source, labels=()):
        from yay.openers.base import Openers, SearchpathFromGraph

        class Config(config.Config):

            def setup_openers(self):
                self.add({"yay": {"searchpath": self.searchpath or []}})
                self.openers = Openers(
                    searchpath=SearchpathFromGraph(self.yay.searchpath))

        c = Config()
        if self.builtins:
            for k, v in self.builtins.items():
                c.builtins[k] = v
                v.parent = c
        c.load(io.StringIO(source), labels=labels)
        return c

    def _resolve(self, source):
        return self._parse(source).resolve()

    def _config(self, source):
        fd, path = tempfile.mkstemp()
        os.write(fd, source.encode("utf-8"))
        os.close(fd)
        self.addCleanup(os.unlink, path)
        return path

    def assertResolves(self, source, expected):
        self.assertEqual(self._resolve(source), expected)

    if not hasattr(unittest.TestCase, "addCleanup"):
        def __init__(self, *args, **kwargs):
            self.cleanups = []
            super(TestCase, self).__init__(*args, **kwargs)

        def addCleanup(self, func, *args, **kwargs):
            self.cleanups.append((func, args, kwargs))

        def tearDown(self):
            for func, args, kwargs in reversed(self.cleanups):
                try:
                    func(*args, **kwargs)
                except:
                    pass

        def assertIn(self, a, b):
            assert a in b, "%r not in %r" % (a, b)

        def assertRegex(self, text, expected_regex, msg=None):
            """Fail the test unless the text matches the regular expression."""
            import re
            if isinstance(expected_regex, basestring):
                expected_regex = re.compile(expected_regex)
            if not expected_regex.search(text):
                msg = msg or "Regex didn't match"
                msg = '%s: %r not found in %r' % (msg, expected_regex.pattern, text)
                raise self.failureException(msg)

        assertRaisesRegexp = assertRegex
