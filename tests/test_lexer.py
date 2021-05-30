import unittest
import inspect

from koi.lexer import Tests


class TestLexer(unittest.TestCase):
    pass


for name, func in inspect.getmembers(Tests, predicate=inspect.isfunction):
    if name.startswith("test_"):
        setattr(TestLexer, name, func)
