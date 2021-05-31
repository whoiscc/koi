# koi/__init__.py - koi package


class Tests:  # pragma: no cover
    @staticmethod
    def test_doctest(_):
        import doctest

        doctest.testmod()
