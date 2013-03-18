import unittest
from .base import parse, resolve
from yay import errors


class TestResolveParadoxes(unittest.TestCase):

    """
    Because of the lazily evaluated nature of yay there are various scenarios
    where a situation similar to the grandfather paradox occurs.

    Conditionals might alter variables that the conditional depend on.

    This would lead to inconsistent state, and thus is considered a critical
    error.
    """

    def test_include_preventing_itself(self):
        """
        foo is 1, 'example' is included
        If 'example' is included, then foo is 0
        So 'example' shouldn't be included
        """
        t = parse("""
                foo: 1
                include "example" if foo else []
                """,
                example="""
                foo: 0
                """)
        self.assertRaises(errors.ParadoxError, t.resolve)

    def test_include_preventing_itself_but_overriden(self):
        """
        This should work as foo: is not masked by an import
        """
        t = parse("""
                include "example" if foo else []
                foo: 1
                """,
                example="""
                foo: 0
                """)
        self.assertEqual(t.get("foo").as_int(), 1)

    def test_select_preventing_itself(self):
        """
        foo is 'bar', so select returns a dict with foo key
        but now foo is 'qux' so foo shouldn't have changed
        """
        t = parse("""
            out:
                foo: bar

            out:
                select out.foo:
                    bar:
                        foo: qux
            """)

        self.assertRaises(errors.ParadoxError, t.resolve)

    def test_select_preventing_itself_overriden(self):
        """
        foo is 'bar', so select returns a dict with foo key
        but now foo is 'qux' so foo shouldn't have changed
        """
        t = parse("""
            out:
                foo: bar

            out:
                select out.foo:
                    bar:
                        foo: qux

            out:
                foo: ok
            """)

        self.assertEqual(t.get("out").get("foo").resolve(), "ok")

    def test_if_preventing_itself(self):
        """
        bar is set to 0 when foo is 1, but as foo is only 1 when bar is 1..
        """
        t = parse("""
            bar: 1
            foo: {{ bar }}

            if foo:
                bar: 0
            """)

        self.assertRaises(errors.ParadoxError, t.resolve)

    def test_if_preventing_itself_overriden(self):
        """ This shouldn't be considered inconsistent either """
        t = parse("""
            bar: 1
            foo: {{ bar }}

            if foo:
                bar: 0

            bar: 1
            """)

        self.assertEqual(t.get("bar").resolve(), 1)

    def test_include_var_changes_in_include(self):
        t = parse("""
            lol: foo
            include lol
            """,
            foo="""
            lol: bar
            """,
            bar="""
            never: ever
            """)

        self.assertRaises(errors.ParadoxError, t.get, "never")
