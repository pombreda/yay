import unittest
from yay import parser
from yay.ast import *

class MockRoot(Root):

    def __init__(self, node):
        super(MockRoot, self).__init__(node)
        self.data = {}

    def add(self, key, value):
        self.data[key] = value

    def parse(self, path):
        return parser.parse(self.data[path], debug=0)


def resolve(value, **kwargs):
    root = MockRoot(parser.parse(value, debug=0))
    for k, v in kwargs.items():
        root.add(k, v)
    return root.resolve()
    #print repr(parser.parse(value, debug=0))


class TestResolver(unittest.TestCase):

    def test_very_lazy(self):
        res = resolve("""
            a: b
            b: {{ a }}
            a: c
            """)
        self.assertEqual(res['b'], "c")

    def test_nested_dict(self):
        res = resolve("""
        a:
            b: c
        """)
        self.assertEqual(res, {"a": {"b": "c"}})

    def test_sample1(self):
        res = resolve("""
        key1: value1

        key2: value2

        key3:
          - item1
          - item2
          - item3

        key4:
            key5:
                key6: key7
        """)
        self.assertEqual(res, {
            "key1": "value1",
            "key2": "value2",
            "key3": ["item1", "item2", "item3"],
            "key4": {
                "key5": {
                    "key6": "key7",
                    }
                }
            })

    def test_list_of_dicts(self):
        res = resolve("""
            a:
              - b
              - c: d
              - e
              """)
        self.assertEqual(res, {"a": [
          "b",
          {"c": "d"},
          "e"
          ]})

    def test_list_of_complex_dicts(self):
        res = resolve("""
            a:
              - b
              - c:
                - e
                - f
            """)
        self.assertEqual(res, {
          "a": [
            "b",
            {"c": ["e", "f"]},
          ]})

    def test_list_of_multikey_dicts(self):
        res = resolve("""
            a:
              - b
              - c: d
                e: f
              - g
              """)
        self.assertEqual(res, {"a": [
          "b",
          {"c": "d", "e": "f"},
          "g",
          ]})

    def test_list_of_dicts_with_lists_in(self):
        res = resolve("""
            a:
             - b: c
               d:
                 - e
                 - f
                 - g
              """)
        self.assertEqual(res, {
          "a": [{
              "b": "c",
              "d": [ "e", "f", "g" ],
              }]
          })

    def test_simple_overlay(self):
        res = resolve("""
        foo:
          a: b

        foo:
          c: d
        """)
        self.assertEqual(res, {
            "foo": {"a": "b", "c": "d"},
            })

    def test_mix(self):
        res = resolve("""
        range:
          - 1
          - 2

        bar:
            % for x in range
                - {{x}}

        quux:
            - a
            - b
        """)

        self.assertEqual(res, {
            "range": ['1', '2'],
            "bar": ['1', '2'],
            "quux": ['a', 'b'],
            })

    def test_nested_for(self):
        # FIXME: WE WANT TO DO MATHS HERE
        res = resolve("""
        range:
          - 1
          - 2

        bar:
            % for x in range
              % for y in range
                - {{x + y}}
        """)
        self.assertEquals(res['bar'], ['11', '12', '21', '22'])

    def test_template_variable_between_scalars(self):
        self.assertEqual(
          resolve("name: doug\nbar: hello {{ name }} !\n")['bar'],
          "hello doug !"
          )

    def test_template_multiple_variables(self):
        self.assertEqual(
          resolve("name: doug\nname2: steve\nbar: {{ name }} and {{ name2 }}!\n")['bar'],
          "doug and steve!"
          )

    def test_template_expr_equals(self):
        res = resolve("bar: {{ 1 == 2}}\n")
        self.assertEqual(res, {"bar": 'False'})

    def test_template_expr_not_equals(self):
        res = resolve("bar: {{ 1 != 2}}\n")
        self.assertEqual(res, {"bar": 'True'})

    def test_template_expr_variables_equals(self):
        res = resolve("""
          a: 1
          b: 1
          c: {{ a == b}}
          """)
        self.assertEqual(res['c'], 'True')

    def test_template_attributeref(self):
        res = resolve("""
            a:
              b: hello
            bar: {{ a.b }}
            """)
        self.assertEqual(res['bar'], 'hello')

    def test_template_subscription_index(self):
        res = resolve("""
            a:
              - foo
            bar: {{ a[0] }}
            """)
        self.assertEqual(res['bar'], 'foo')

    def test_template_subscription_string(self):
        res = resolve("""
            a:
              b: hello
            bar: {{ a['b'] }}
            """)
        self.assertEqual(res['bar'], 'hello')

    def test_template_subscription_variable(self):
        res = resolve("""
            a:
              b: hello
            c: b
            bar: {{ a[c] }}
            """)
        self.assertEqual(res['bar'], 'hello')

    def test_template_subscription_variable(self):
        res = resolve("""
            a:
              b: hello
            c: b
            bar: {{ a[c] }}
            """)
        self.assertEqual(res['bar'], 'hello')

    def test_extend(self):
        res = resolve("""
            resources:
                - Foo:
                     bar: baz
            extend resources:
                 - Qux:
                      bar: baz
            """)
        self.assertEquals(res['resources'], [
            {"Foo": {"bar": "baz"}},
            {"Qux": {"bar": "baz"}}
            ])

    def test_simple_include(self):
        res = resolve("""
            % include 'foo'
            """,
            foo="""
            hello: world
            """)
        self.assertEqual(res, {"hello": "world"})

    def test_include_with_extends(self):
        res = resolve("""
            % include 'foo'
            extend resources:
             - 3
            """,
            foo="""
            resources:
              - 1
              - 2
            """)
        self.assertEqual(res, {"resources": ['1','2','3']})

    def test_include_include(self):
        res = resolve("""
            % include 'foo'
            """,
            foo="""
            %include 'bar'
            """,
            bar="""
            hello: world
            """)
        self.assertEqual(res, {"hello": "world"})

    def test_include_include_2(self):
        res = resolve("""
            % include 'foo'
            hello: world
            """,
            foo="""
            %include 'bar'
            hello: quark
            wibble: wobble
            """,
            bar="""
            hello: qux
            foo: bar
            """)
        self.assertEqual(res, {"wibble": "wobble", "hello": "world", "foo": "bar"})
