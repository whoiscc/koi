import unittest
import inspect

from koi import Tests as KoiTests
from koi.lexer import Tests as LexerTests


koi_tests = unittest.TestSuite()
for Tests in [LexerTests, KoiTests]:

    class TestCase(unittest.TestCase):
        pass

    for name, func in inspect.getmembers(Tests, predicate=inspect.isfunction):
        if name.startswith("test_"):
            setattr(TestCase, name, func)
    koi_tests.addTest(unittest.defaultTestLoader.loadTestsFromTestCase(TestCase))

del TestCase
