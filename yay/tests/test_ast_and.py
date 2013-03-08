# Copyright 2013 Isotoma Limited
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
from yay.ast import And, Literal
from yay.tests.test_ast_common import DynamicLiteral


class TestAndSimplification(unittest.TestCase):

    def test_both_dynamic(self):
        n = And(DynamicLiteral('left'), DynamicLiteral('right'))
        res = n.simplify()

        self.assertTrue(isinstance(res, And))
        self.assertNotEqual(res, n)
        self.assertEqual(n.left.literal, 'left')
        self.assertEqual(n.right.literal, 'right')

    def test_dynamic_left_right_true(self):
        n = And(DynamicLiteral('left'), Literal(True))
        res = n.simplify()

        self.assertTrue(isinstance(res, DynamicLiteral))
        self.assertEqual(res.literal, 'left')

    def test_dynamic_left_right_false(self):
        n = And(DynamicLiteral('left'), Literal(False))
        res = n.simplify()

        self.assertTrue(isinstance(res, Literal))
        self.assertEqual(res.literal, False)

    def test_dynamic_right_left_true(self):
        n = And(Literal(True), DynamicLiteral('right'))
        res = n.simplify()

        self.assertTrue(isinstance(res, DynamicLiteral))
        self.assertEqual(res.literal, 'right')

    def test_dynamic_right_left_false(self):
        n = And(Literal(False), DynamicLiteral('right'))
        res = n.simplify()

        self.assertTrue(isinstance(res, Literal))
        self.assertEqual(res.literal, False)

    def test_both_constant(self):
        n = And(Literal(False), Literal(True))
        res = n.simplify()

        self.assertTrue(isinstance(res, Literal))
        self.assertEqual(res.literal, False)


class TestAndResolve(unittest.TestCase):

    def test_if_true_true(self):
        n = And(Literal(True), Literal(True))
        self.assertEqual(n.resolve(), True)

    def test_if_true_false(self):
        n = And(Literal(True), Literal(False))
        self.assertEqual(n.resolve(), False)

    def test_if_false_true(self):
        n = And(Literal(False), Literal(True))
        self.assertEqual(n.resolve(), False)

    def test_if_false_false(self):
        n = And(Literal(False), Literal(False))
        self.assertEqual(n.resolve(), False)

