# Novlang Compiler
# Lexer: converts Novlang source code into a stream of tokens.

class NovlangError(Exception):
    pass


class Token:
    def __init__(self, type_, value, line):
        self.type = type_
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, line={self.line})"


KEYWORDS = {
    'let': 'LET',
    'func': 'FUNC',
    'return': 'RETURN',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'print': 'PRINT',
    'true': 'TRUE',
    'false': 'FALSE',
}

TWO_CHAR_OPS = {
    '==': 'EQEQ',
    '!=': 'NEQ',
    '<=': 'LTE',
    '>=': 'GTE',
    '&&': 'AND',
    '||': 'OR',
}

ONE_CHAR_OPS = {
    '+': 'PLUS',
    '-': 'MINUS',
    '*': 'STAR',
    '/': 'SLASH',
    '%': 'PERCENT',
    '=': 'EQ',
    '<': 'LT',
    '>': 'GT',
    '!': 'NOT',
    '(': 'LPAREN',
    ')': 'RPAREN',
    '{': 'LBRACE',
    '}': 'RBRACE',
    ';': 'SEMI',
    ',': 'COMMA',
}

ESCAPES = {'n': '\n', 't': '\t', '"': '"', '\\': '\\'}


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos = 0
        self.line = 1
        self.tokens = []

    def error(self, msg):
        raise NovlangError(f"Lexer error on line {self.line}: {msg}")

    def peek(self, offset=0):
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else '\0'

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def tokenize(self):
        while self.pos < len(self.source):
            ch = self.peek()
            if ch in ' \t\r\n':
                self.advance()
            elif ch == '/' and self.peek(1) == '/':
                self.skip_line_comment()
            elif ch == '/' and self.peek(1) == '*':
                self.skip_block_comment()
            elif ch.isdigit():
                self.read_number()
            elif ch == '"':
                self.read_string()
            elif ch.isalpha() or ch == '_':
                self.read_identifier()
            elif self.peek(0) + self.peek(1) in TWO_CHAR_OPS:
                op = self.peek(0) + self.peek(1)
                self.tokens.append(Token(TWO_CHAR_OPS[op], op, self.line))
                self.advance()
                self.advance()
            elif ch in ONE_CHAR_OPS:
                self.tokens.append(Token(ONE_CHAR_OPS[ch], ch, self.line))
                self.advance()
            else:
                self.error(f"Unexpected character '{ch}'")
        self.tokens.append(Token('EOF', None, self.line))
        return self.tokens

    def skip_line_comment(self):
        while self.pos < len(self.source) and self.peek() != '\n':
            self.advance()

    def skip_block_comment(self):
        self.advance()
        self.advance()  # consume /*
        while self.pos < len(self.source):
            if self.peek() == '*' and self.peek(1) == '/':
                self.advance()
                self.advance()
                return
            self.advance()
        self.error("Unterminated block comment")

    def read_number(self):
        start_line = self.line
        text = ''
        while self.peek().isdigit():
            text += self.advance()
        if self.peek() == '.' and self.peek(1).isdigit():
            text += self.advance()
            while self.peek().isdigit():
                text += self.advance()
            self.tokens.append(Token('NUMBER', float(text), start_line))
        else:
            self.tokens.append(Token('NUMBER', int(text), start_line))

    def read_string(self):
        start_line = self.line
        self.advance()  # opening quote
        text = ''
        while self.pos < len(self.source) and self.peek() != '"':
            ch = self.advance()
            if ch == '\\':
                esc = self.advance()
                if esc in ESCAPES:
                    text += ESCAPES[esc]
                else:
                    self.error(f"Unknown escape '\\{esc}'")
            else:
                text += ch
        if self.pos >= len(self.source):
            self.error("Unterminated string")
        self.advance()  # closing quote
        self.tokens.append(Token('STRING', text, start_line))

    def read_identifier(self):
        start_line = self.line
        text = ''
        while self.peek().isalnum() or self.peek() == '_':
            text += self.advance()
        tok_type = KEYWORDS.get(text, 'IDENT')
        self.tokens.append(Token(tok_type, text, start_line))
