# Novlang Compiler
# Parser: recursive-descent parser that turns the token stream into an AST.
#
# Grammar:
#   program     -> statement*
#   statement   -> letDecl | funcDecl | ifStmt | whileStmt | printStmt
#                | returnStmt | block | exprStmt
#   letDecl     -> "let" IDENT "=" expr ";"
#   funcDecl    -> "func" IDENT "(" params? ")" block
#   ifStmt      -> "if" "(" expr ")" statement ("else" statement)?
#   whileStmt   -> "while" "(" expr ")" statement
#   printStmt   -> "print" ( "(" expr ")" | expr ) ";"
#   returnStmt  -> "return" expr ";"
#   block       -> "{" statement* "}"
#   exprStmt    -> expr ";"
#   expr        -> assignment
#   assignment  -> logicalOr ( "=" assignment )?
#   logicalOr   -> logicalAnd ( "||" logicalAnd )*
#   logicalAnd  -> equality ( "&&" equality )*
#   equality    -> comparison ( ( "==" | "!=" ) comparison )*
#   comparison  -> term ( ( "<" | "<=" | ">" | ">=" ) term )*
#   term        -> factor ( ( "+" | "-" ) factor )*
#   factor      -> unary ( ( "*" | "/" | "%" ) unary )*
#   unary       -> ( "!" | "-" ) unary | call
#   call        -> primary ( "(" args? ")" )*
#   primary     -> NUMBER | STRING | "true" | "false" | IDENT | "(" expr ")"

from lexer import NovlangError
import ast_nodes as ast


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ----- helpers -----
    def error(self, msg):
        tok = self.peek()
        raise NovlangError(f"Parse error on line {tok.line}: {msg}")

    def peek(self):
        return self.tokens[self.pos]

    def previous(self):
        return self.tokens[self.pos - 1]

    def at_end(self):
        return self.peek().type == 'EOF'

    def check(self, type_):
        return not self.at_end() and self.peek().type == type_

    def match(self, *types):
        for t in types:
            if self.check(t):
                self.pos += 1
                return True
        return False

    def consume(self, type_, msg):
        if self.check(type_):
            self.pos += 1
            return self.previous()
        self.error(msg)

    # ----- entry -----
    def parse(self):
        statements = []
        while not self.at_end():
            statements.append(self.declaration())
        return ast.Program(statements)

    def declaration(self):
        if self.match('LET'):
            return self.let_decl()
        if self.match('FUNC'):
            return self.func_decl()
        return self.statement()

    def let_decl(self):
        line = self.previous().line
        name = self.consume('IDENT', "Expected variable name after 'let'").value
        self.consume('EQ', "Expected '=' after variable name")
        value = self.expr()
        self.consume('SEMI', "Expected ';' after variable declaration")
        return ast.LetDecl(name, value, line)

    def func_decl(self):
        line = self.previous().line
        name = self.consume('IDENT', "Expected function name after 'func'").value
        self.consume('LPAREN', "Expected '(' after function name")
        params = []
        if not self.check('RPAREN'):
            params.append(self.consume('IDENT', "Expected parameter name").value)
            while self.match('COMMA'):
                params.append(self.consume('IDENT', "Expected parameter name").value)
        self.consume('RPAREN', "Expected ')' after parameters")
        body = self.block()
        return ast.FuncDecl(name, params, body, line)

    def statement(self):
        if self.match('PRINT'):
            return self.print_stmt()
        if self.match('IF'):
            return self.if_stmt()
        if self.match('WHILE'):
            return self.while_stmt()
        if self.match('RETURN'):
            return self.return_stmt()
        if self.check('LBRACE'):
            return self.block()
        return self.expr_stmt()

    def print_stmt(self):
        line = self.previous().line
        if self.match('LPAREN'):
            value = self.expr()
            self.consume('RPAREN', "Expected ')' after print value")
        else:
            value = self.expr()
        self.consume('SEMI', "Expected ';' after print statement")
        return ast.PrintStmt(value, line)

    def if_stmt(self):
        line = self.previous().line
        self.consume('LPAREN', "Expected '(' after 'if'")
        condition = self.expr()
        self.consume('RPAREN', "Expected ')' after if condition")
        then_branch = self.statement()
        else_branch = self.statement() if self.match('ELSE') else None
        return ast.IfStmt(condition, then_branch, else_branch, line)

    def while_stmt(self):
        line = self.previous().line
        self.consume('LPAREN', "Expected '(' after 'while'")
        condition = self.expr()
        self.consume('RPAREN', "Expected ')' after while condition")
        body = self.statement()
        return ast.WhileStmt(condition, body, line)

    def return_stmt(self):
        line = self.previous().line
        value = self.expr()
        self.consume('SEMI', "Expected ';' after return value")
        return ast.ReturnStmt(value, line)

    def block(self):
        line = self.consume('LBRACE', "Expected '{'").line
        statements = []
        while not self.check('RBRACE') and not self.at_end():
            statements.append(self.declaration())
        self.consume('RBRACE', "Expected '}' to close block")
        return ast.Block(statements, line)

    def expr_stmt(self):
        line = self.peek().line
        value = self.expr()
        self.consume('SEMI', "Expected ';' after expression")
        return ast.ExprStmt(value, line)

    # ----- expressions -----
    def expr(self):
        return self.assignment()

    def assignment(self):
        node = self.logical_or()
        if self.match('EQ'):
            line = self.previous().line
            value = self.assignment()
            if isinstance(node, ast.Variable):
                return ast.Assign(node.name, value, line)
            self.error("Invalid assignment target")
        return node

    def logical_or(self):
        node = self.logical_and()
        while self.match('OR'):
            node = ast.Binary(node, 'OR', self.logical_and(), self.previous().line)
        return node

    def logical_and(self):
        node = self.equality()
        while self.match('AND'):
            node = ast.Binary(node, 'AND', self.equality(), self.previous().line)
        return node

    def equality(self):
        node = self.comparison()
        while self.match('EQEQ', 'NEQ'):
            op = self.previous().type
            node = ast.Binary(node, op, self.comparison(), self.previous().line)
        return node

    def comparison(self):
        node = self.term()
        while self.match('LT', 'LTE', 'GT', 'GTE'):
            op = self.previous().type
            node = ast.Binary(node, op, self.term(), self.previous().line)
        return node

    def term(self):
        node = self.factor()
        while self.match('PLUS', 'MINUS'):
            op = self.previous().type
            node = ast.Binary(node, op, self.factor(), self.previous().line)
        return node

    def factor(self):
        node = self.unary()
        while self.match('STAR', 'SLASH', 'PERCENT'):
            op = self.previous().type
            node = ast.Binary(node, op, self.unary(), self.previous().line)
        return node

    def unary(self):
        if self.match('NOT', 'MINUS'):
            op = self.previous().type
            return ast.Unary(op, self.unary(), self.previous().line)
        return self.call()

    def call(self):
        node = self.primary()
        while self.match('LPAREN'):
            line = self.previous().line
            args = []
            if not self.check('RPAREN'):
                args.append(self.expr())
                while self.match('COMMA'):
                    args.append(self.expr())
            self.consume('RPAREN', "Expected ')' after arguments")
            if isinstance(node, ast.Variable):
                node = ast.Call(node.name, args, line)
            else:
                self.error("Can only call functions by name")
        return node

    def primary(self):
        tok = self.peek()
        if self.match('NUMBER', 'STRING'):
            t = self.previous()
            return ast.Literal(t.value, t.line)
        if self.match('TRUE'):
            return ast.Literal(True, self.previous().line)
        if self.match('FALSE'):
            return ast.Literal(False, self.previous().line)
        if self.match('IDENT'):
            return ast.Variable(self.previous().value, self.previous().line)
        if self.match('LPAREN'):
            node = self.expr()
            self.consume('RPAREN', "Expected ')' after expression")
            return node
        self.error(f"Unexpected token '{tok.value}'")
