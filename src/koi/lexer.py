# koi/lexer.py - Lexical parser for Koi language
from dataclasses import dataclass, replace
from typing import Any, Tuple
import re


@dataclass(frozen=True)
class Token:
    kind: str
    position: Tuple[int, int]
    value: Any = None


class LexError(Exception):
    def __init__(self, position):
        row, col = position
        super().__init__(f"lexical error at row {row + 1}, column {col + 1}")
        self.position = position


def lexical_parse(source):
    token_stream = source
    for do_pass in (
        # TODO
        break_line_pass,
        string_literal_pass,
        comment_pass,
        indent_level_pass,
    ):
        token_stream = do_pass(token_stream)
    yield from token_stream


# take original source file, yield each line with line breaks
# yield eof with its position
def break_line_pass(source):
    for row, line in enumerate(source.splitlines(keepends=True)):
        yield Token(kind="line", value=line, position=(row, 0))
    # TODO: other kinds of break
    eof_position = (row, len(line)) if source[-1] != "\n" else (row + 1, 0)
    yield Token(kind="eof", position=eof_position)


# extract string literal from source
def string_literal_pass(token_gen):
    accumulated, string_position, close_quote = None, None, None
    for token in token_gen:
        if token.kind == "eof":
            if accumulated:
                raise LexError(token.position)
            yield token
            return
        assert token.kind == "line"

        line = token.value
        row, col_offset = token.position
        while line:
            if accumulated is None:
                offset = line.find('"')
                if offset < 0:
                    yield Token(kind="line", value=line, position=(row, col_offset))
                    break
                pre_string, line = line[:offset], line[offset + 1 :]
                if pre_string:
                    yield Token(
                        kind="line", value=pre_string, position=(row, col_offset)
                    )
                col_offset += offset + 1  # for open quote
                accumulated = ""
                string_position = row, col_offset
                close_quote = '"'  # TODO
            else:
                match = re.search(rf"[^\\]?({close_quote})", line)
                if not match:
                    accumulated += line
                    break
                offset = match.start(1)
                string_tail, line = (
                    line[:offset],
                    line[offset + len(close_quote) :],
                )
                if string_tail:
                    accumulated += string_tail
                col_offset += offset + len(close_quote)
                yield Token(kind="string", value=accumulated, position=string_position)
                accumulated = string_position = close_quote = None


# skip comment and empty lines, remove trailing spaces and line break
def comment_pass(token_gen):
    for token in token_gen:
        if token.kind != "line":
            yield token
            continue
        pure_line = token.value.split(";")[0].rstrip()
        if pure_line.strip():
            yield replace(token, value=pure_line)


# convert indent in the front of line into level token
def indent_level_pass(token_gen):
    levels = [0]
    is_first = True  # prefer this way than enumerate
    for token in token_gen:
        if token.kind == "eof":
            for level in levels:
                if level:
                    yield Token(kind="close_level", position=token.position)
            yield token
            return
        if token.kind != "line":
            yield token
            continue

        rest = token.value.lstrip()
        token_level = len(token.value) - len(rest)
        if is_first and token_level:
            raise LexError(token.position)
        is_first = False

        row, col = token.position
        level_position = row, col + token_level
        if token_level > levels[-1]:
            yield Token(kind="open_level", position=level_position)
            levels.append(token_level)
        elif token_level < levels[-1]:
            if token_level not in levels:
                raise LexError(level_position)
            while levels[-1] != token_level:
                yield Token(kind="close_level", position=level_position)
                levels.pop()
        yield Token(kind="line", value=rest, position=level_position)


if __name__ == "__main__":
    from sys import argv

    with open(argv[1]) as source_file:
        token_stream = lexical_parse(source_file.read())
    for token in token_stream:
        print(token)


class Tests:
    @staticmethod
    def internal_match_break_line_pass_result(
        t, source, trailing=False, extra="", string_pass=False
    ):
        second_row = 1 if not extra else 2
        if not string_pass:
            tokens = list(comment_pass(break_line_pass(source)))
        else:
            tokens = list(comment_pass(string_literal_pass(break_line_pass(source))))
        eof_position = (second_row + 1, 0) if trailing else (second_row, 6)
        t.assertEqual(
            tokens,
            [
                Token(kind="line", value="hello", position=(0, 0)),
                Token(kind="line", value="cowsay", position=(second_row, 0)),
                Token(kind="eof", position=eof_position),
            ],
        )

    @staticmethod
    def test_break_line_pass(t):
        source = "hello\ncowsay"
        Tests.internal_match_break_line_pass_result(t, source)

    @staticmethod
    def test_break_line_tailing_line_break(t):
        source = "hello\ncowsay\n"
        Tests.internal_match_break_line_pass_result(t, source, trailing=True)

    @staticmethod
    def test_break_line_extra_line_break(t):
        source = "hello\n\ncowsay"
        Tests.internal_match_break_line_pass_result(t, source, extra="\n")

    @staticmethod
    def test_break_line_comment(t):
        comment = "; here comes the name\n"
        source = f"hello\n{comment}cowsay"
        Tests.internal_match_break_line_pass_result(t, source, extra=comment)

    @staticmethod
    def test_indent_level_pass(t):
        lines = [
            Token(kind="line", position=(0, 0), value="hello"),
            Token(kind="line", position=(1, 0), value="  cowsay"),
            Token(kind="eof", position=(2, 0)),
        ]
        tokens = list(indent_level_pass(lines))
        t.assertEqual(
            tokens,
            [
                Token(kind="line", position=(0, 0), value="hello"),
                Token(kind="open_level", position=(1, 2)),
                Token(kind="line", position=(1, 2), value="cowsay"),
                Token(kind="close_level", position=(2, 0)),
                Token(kind="eof", position=(2, 0)),
            ],
        )

    @staticmethod
    def test_fib_level(t):
        from pathlib import Path

        source = (Path(__file__).parent / ".." / ".." / "misc" / "fib.koi").read_text()
        tokens = list(indent_level_pass(comment_pass(break_line_pass(source))))
        t.assertEqual(
            [token.kind for token in tokens],
            [
                "line",
                "open_level",
                "line",
                "open_level",
                "line",
                "line",
                "close_level",
                "line",
                "close_level",
                "eof",
            ],
        )

    @staticmethod
    def test_throw_on_initial_indent(t):
        lines = [
            Token(kind="line", value="  hello", position=(0, 0)),
            Token(kind="eof", position=(0, 7)),
        ]
        t.assertRaises(LexError, lambda: list(indent_level_pass(lines)))

    @staticmethod
    def test_throw_on_dedent_mismatch(t):
        lines = [
            Token(kind="line", value="hello", position=(0, 0)),
            Token(kind="line", value="  cowsay", position=(1, 0)),
            Token(kind="line", value=" end hello", position=(2, 0)),
            Token(kind="eof", position=(3, 0)),
        ]
        t.assertRaises(LexError, lambda: list(indent_level_pass(lines)))

    @staticmethod
    def test_trailing_comment(t):
        source = "hello  ; to who?\ncowsay"
        Tests.internal_match_break_line_pass_result(t, source)

    @staticmethod
    def test_string_pass_without_string(t):
        source = "hello\ncowsay"
        Tests.internal_match_break_line_pass_result(t, source, string_pass=True)

    @staticmethod
    def test_single_line_string(t):
        lines = break_line_pass('say "Hello!"\n')
        tokens = list(string_literal_pass(lines))
        t.assertEqual(
            tokens,
            [
                Token(kind="line", value="say ", position=(0, 0)),
                Token(kind="string", value="Hello!", position=(0, 5)),
                Token(kind="line", value="\n", position=(0, 12)),
                Token(kind="eof", position=(1, 0)),
            ],
        )

    @staticmethod
    def test_single_line_multiple_string(t):
        lines = break_line_pass('say "Hello!", to: "cowsay"\n')
        tokens = list(string_literal_pass(lines))
        t.assertEqual(
            tokens,
            [
                Token(kind="line", value="say ", position=(0, 0)),
                Token(kind="string", value="Hello!", position=(0, 5)),
                Token(kind="line", value=", to: ", position=(0, 12)),
                Token(kind="string", value="cowsay", position=(0, 19)),
                Token(kind="line", value="\n", position=(0, 26)),
                Token(kind="eof", position=(1, 0)),
            ],
        )

    @staticmethod
    def test_multiline_string(t):
        lines = break_line_pass('say "\nDear cowsay:\n  Hello!\n"\n')
        tokens = list(string_literal_pass(lines))
        t.assertEqual(
            tokens,
            [
                Token(kind="line", value="say ", position=(0, 0)),
                Token(
                    kind="string", value="\nDear cowsay:\n  Hello!\n", position=(0, 5)
                ),
                Token(kind="line", value="\n", position=(3, 1)),
                Token(kind="eof", position=(4, 0)),
            ],
        )

    @staticmethod
    def test_throw_on_unclosed_string(t):
        lines = break_line_pass('say "Hello!\n')
        t.assertRaises(LexError, lambda: list(string_literal_pass(lines)))
