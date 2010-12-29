import unittest
from yay.config import *

class TestListOperations(unittest.TestCase):

    def test_list(self):
        l = List([Boxed(1), Boxed(2), Boxed(3)])

        self.failUnlessEqual(l.resolve(), [1, 2, 3])

    def test_list_append(self):
        l = List([Boxed(1), Boxed(2), Boxed(3)])
        a = Append([Boxed(4), Boxed(5)])
        a.chain = l

        self.failUnlessEqual(a.resolve(), [1,2,3,4,5])

    def test_list_remove(self):
        l = List([Boxed(1), Boxed(2), Boxed(3)])
        r = Remove([Boxed(2)])
        r.chain = l

        self.failUnlessEqual(r.resolve(), [1, 3])
