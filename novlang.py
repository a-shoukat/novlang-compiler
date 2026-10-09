#!/usr/bin/env python3
# Novlang Compiler - main entry point.
# Usage: python3 novlang.py <program.nov>

import sys
from lexer import Lexer, NovlangError
from parser import Parser
from interpreter import Interpreter


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 novlang.py <program.nov>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r') as f:
            source = f.read()
    except FileNotFoundError:
        print(f"Error: file '{sys.argv[1]}' not found.", file=sys.stderr)
        sys.exit(1)

    try:
        tokens = Lexer(source).tokenize()
        program = Parser(tokens).parse()
        Interpreter().run(program)
    except NovlangError as e:
        print(e, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
