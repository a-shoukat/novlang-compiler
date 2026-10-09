# Novlang Compiler
# AST node definitions. Every node carries its source line for error messages.

class Node:
    def __init__(self, line=0):
        self.line = line


# ---------------- Statements ----------------

class Program(Node):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements


class LetDecl(Node):
    def __init__(self, name, value, line):
        super().__init__(line)
        self.name = name
        self.value = value


class FuncDecl(Node):
    def __init__(self, name, params, body, line):
        super().__init__(line)
        self.name = name
        self.params = params
        self.body = body


class IfStmt(Node):
    def __init__(self, condition, then_branch, else_branch, line):
        super().__init__(line)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


class WhileStmt(Node):
    def __init__(self, condition, body, line):
        super().__init__(line)
        self.condition = condition
        self.body = body


class PrintStmt(Node):
    def __init__(self, value, line):
        super().__init__(line)
        self.value = value


class ReturnStmt(Node):
    def __init__(self, value, line):
        super().__init__(line)
        self.value = value


class Block(Node):
    def __init__(self, statements, line):
        super().__init__(line)
        self.statements = statements


class ExprStmt(Node):
    def __init__(self, expr, line):
        super().__init__(line)
        self.expr = expr


# ---------------- Expressions ----------------

class Binary(Node):
    def __init__(self, left, op, right, line):
        super().__init__(line)
        self.left = left
        self.op = op        # token type: PLUS, EQEQ, ...
        self.right = right


class Unary(Node):
    def __init__(self, op, operand, line):
        super().__init__(line)
        self.op = op        # NOT or MINUS
        self.operand = operand


class Literal(Node):
    def __init__(self, value, line):
        super().__init__(line)
        self.value = value


class Variable(Node):
    def __init__(self, name, line):
        super().__init__(line)
        self.name = name


class Assign(Node):
    def __init__(self, name, value, line):
        super().__init__(line)
        self.name = name
        self.value = value


class Call(Node):
    def __init__(self, name, args, line):
        super().__init__(line)
        self.name = name
        self.args = args
