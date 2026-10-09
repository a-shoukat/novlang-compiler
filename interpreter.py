# Novlang Compiler
# Interpreter: tree-walk interpreter that executes the AST directly.

from lexer import NovlangError
import ast_nodes as ast


class ReturnSignal(Exception):
    def __init__(self, value):
        self.value = value


class Environment:
    """Lexically scoped variable store (chain of scopes)."""
    def __init__(self, parent=None):
        self.values = {}
        self.parent = parent

    def define(self, name, value):
        self.values[name] = value

    def get(self, name, line):
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name, line)
        raise NovlangError(f"Runtime error on line {line}: Undefined variable '{name}'")

    def set(self, name, value, line):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent:
            self.parent.set(name, value, line)
            return
        raise NovlangError(f"Runtime error on line {line}: Undefined variable '{name}'")


class FuncValue:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def __repr__(self):
        return f"<function {self.name}>"


def is_truthy(value):
    if value is None or value is False:
        return False
    if isinstance(value, (int, float)) and value == 0:
        return False
    if isinstance(value, str) and value == "":
        return False
    return True


def stringify(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, FuncValue):
        return repr(value)
    if value is None:
        return "nil"
    return str(value)


class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self.env = self.globals

    # ----- entry -----
    def run(self, program):
        for stmt in program.statements:
            self.execute(stmt)

    # ----- statements -----
    def execute(self, node):
        if isinstance(node, ast.LetDecl):
            self.env.define(node.name, self.evaluate(node.value))
        elif isinstance(node, ast.FuncDecl):
            self.env.define(node.name, FuncValue(node.name, node.params, node.body, self.env))
        elif isinstance(node, ast.IfStmt):
            if is_truthy(self.evaluate(node.condition)):
                self.execute(node.then_branch)
            elif node.else_branch is not None:
                self.execute(node.else_branch)
        elif isinstance(node, ast.WhileStmt):
            while is_truthy(self.evaluate(node.condition)):
                self.execute(node.body)
        elif isinstance(node, ast.PrintStmt):
            print(stringify(self.evaluate(node.value)))
        elif isinstance(node, ast.ReturnStmt):
            raise ReturnSignal(self.evaluate(node.value))
        elif isinstance(node, ast.Block):
            self.execute_block(node.statements, Environment(self.env))
        elif isinstance(node, ast.ExprStmt):
            self.evaluate(node.expr)
        else:
            raise NovlangError(f"Runtime error on line {node.line}: Unknown statement")

    def execute_block(self, statements, env):
        previous = self.env
        try:
            self.env = env
            for stmt in statements:
                self.execute(stmt)
        finally:
            self.env = previous

    # ----- expressions -----
    def evaluate(self, node):
        if isinstance(node, ast.Literal):
            return node.value
        if isinstance(node, ast.Variable):
            return self.env.get(node.name, node.line)
        if isinstance(node, ast.Assign):
            value = self.evaluate(node.value)
            self.env.set(node.name, value, node.line)
            return value
        if isinstance(node, ast.Unary):
            operand = self.evaluate(node.operand)
            if node.op == 'NOT':
                return not is_truthy(operand)
            if node.op == 'MINUS':
                self.check_number(operand, node.line, "negation")
                return -operand
        if isinstance(node, ast.Binary):
            return self.eval_binary(node)
        if isinstance(node, ast.Call):
            return self.eval_call(node)
        raise NovlangError(f"Runtime error on line {node.line}: Unknown expression")

    def eval_binary(self, node):
        # short-circuit logical operators first
        if node.op == 'OR':
            left = self.evaluate(node.left)
            return left if is_truthy(left) else self.evaluate(node.right)
        if node.op == 'AND':
            left = self.evaluate(node.left)
            return self.evaluate(node.right) if is_truthy(left) else left

        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        op = node.op

        if op == 'EQEQ':
            return left == right
        if op == 'NEQ':
            return left != right

        if op == 'PLUS':
            if isinstance(left, str) or isinstance(right, str):
                return stringify(left) + stringify(right)
            self.check_numbers(left, right, node.line, "+")
            return left + right

        self.check_numbers(left, right, node.line, op)
        if op == 'MINUS':
            return left - right
        if op == 'STAR':
            return left * right
        if op == 'SLASH':
            if right == 0:
                raise NovlangError(f"Runtime error on line {node.line}: Division by zero")
            return left / right
        if op == 'PERCENT':
            if right == 0:
                raise NovlangError(f"Runtime error on line {node.line}: Modulo by zero")
            return left % right
        if op == 'LT':
            return left < right
        if op == 'LTE':
            return left <= right
        if op == 'GT':
            return left > right
        if op == 'GTE':
            return left >= right
        raise NovlangError(f"Runtime error on line {node.line}: Unknown operator")

    def eval_call(self, node):
        callee = self.env.get(node.name, node.line)
        if not isinstance(callee, FuncValue):
            raise NovlangError(f"Runtime error on line {node.line}: '{node.name}' is not a function")
        if len(node.args) != len(callee.params):
            raise NovlangError(
                f"Runtime error on line {node.line}: '{node.name}' expected "
                f"{len(callee.params)} arguments but got {len(node.args)}")
        args = [self.evaluate(a) for a in node.args]
        call_env = Environment(callee.closure)
        for name, value in zip(callee.params, args):
            call_env.define(name, value)
        try:
            self.execute_block(callee.body.statements, call_env)
        except ReturnSignal as ret:
            return ret.value
        return None

    @staticmethod
    def check_number(value, line, where):
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise NovlangError(f"Runtime error on line {line}: '{where}' needs a number")

    @staticmethod
    def check_numbers(left, right, line, op):
        for v in (left, right):
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                raise NovlangError(
                    f"Runtime error on line {line}: Operator '{op}' needs numbers")
