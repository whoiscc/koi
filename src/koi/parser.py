# koi/parser.py - walk through token stream to build syntax tree
from collections import deque


class ParseError(Exception):
    def __init__(self, token):
        super().__init__(f"unexpected {token}")
        self.token = token


class TokenWalker:
    def __init__(self, token_gen):
        self._token_gen = token_gen
        self._buffer = deque()

    def lookahead(self, position=0):
        while len(self._buffer) <= position:
            # assert not lookahead over the end of stream (guard by eof)
            self._buffer.append(next(self._token_gen))
        return self._buffer[position]

    def forward(self, expect_kind=None):
        token = self.lookahead()
        if expect_kind and token.kind != expect_kind:
            raise ParseError(token)
        self._buffer.popleft()


class Tests:  # pragma: no cover
    @staticmethod
    def get_tokens():
        from koi.lexer import Token

        return [Token(kind=f"token{i}", position=(0, i)) for i in range(3)]

    @staticmethod
    def test_lookahead(t):
        tokens = Tests.get_tokens()
        walker = TokenWalker((t for t in tokens))
        t.assertEqual(walker.lookahead(), tokens[0])
        t.assertEqual(walker.lookahead(), tokens[0])
        t.assertEqual(walker.lookahead(1), tokens[1])
        t.assertEqual(walker.lookahead(1), tokens[1])
        walker.forward()
        t.assertEqual(walker.lookahead(), tokens[1])
        t.assertEqual(walker.lookahead(1), tokens[2])

    @staticmethod
    def test_throw_on_unexpected_token(t):
        tokens = Tests.get_tokens()
        walker = TokenWalker((t for t in tokens))
        try:
            walker.forward(expect_kind="token0")
        except ParseError:
            t.fail("unexpected ParseError raised")
        t.assertRaises(ParseError, lambda: walker.forward(expect_kind="cowsay"))
