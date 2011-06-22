import sys
import pyast

if sys.version >= "3":
    basestring = str

### Abstract interfaces


class Node(pyast.Node):
    _debug = False


class Statement(Node):
    pass


class Pattern(Node):
    pass


class Expression(Pattern):
    pass


class Declaration(Statement):
    pass


class Operator(Node):
    pass


class Identifier(Expression):
    name = pyast.field(basestring)


class BlockStatement(Statement):
    body = pyast.seq(Node, null=True)


class Function(Node):
    id = pyast.field(Identifier, null=True)
    params = pyast.seq(Identifier, null=True)
    body = pyast.field((BlockStatement, Expression))
    generator = pyast.field(bool, default=False)
    expression = pyast.field(bool, default=False)

### Misc nodes


class Literal(Expression):
    value = pyast.field((basestring, bool, int, type(None)))


class Program(Node):
    body = pyast.seq(Statement, null=True)


class Property(Node):
    key = pyast.field((Literal, Identifier))
    value = pyast.field(Expression)
    kind = pyast.field(("init", "get", "set"), default="init")


class VariableDeclarator(Node):
    id = pyast.field(Identifier)
    init = pyast.field(Expression, null=True)

### Operators


class UnaryOperator(Operator):
    token = pyast.field(("-", "+", "!", "~", "typeof", "void", "delete"))


class BinaryOperator(Operator):
    token = pyast.field(("==", "!=", "===", "!==", "<", "<=", ">", ">=",
                           "<<", ">>", ">>>", "+", "-", "*", "/", "%", "|",
                           "^", "in", "instanceof", ".."))


class LogicalOperator(Operator):
    token = pyast.field(("||", "&&"))


class AssignmentOperator(Operator):
    token = pyast.field(("=", "+=", "-=", "*=", "/=", "%=", "<<=", ">>=",
                         ">>>=", "|=", "^=", "&="))


class UpdateOperator(Operator):
    token = pyast.field(("++", "--"))

### Declarations


class FunctionDeclaration(Function, Declaration):
    pass

class VariableDeclaration(Declaration):
    kind = pyast.field(("var", "let", "const"))
    declarations = pyast.seq(VariableDeclarator)

### Clauses


class SwitchCase(Node):
    test = pyast.field(Expression, null=True)
    consequent = pyast.seq(Statement)


class CatchClause(Node):
    param = pyast.field(Identifier)
    guard = pyast.field(Expression, null=True)
    body = pyast.field(BlockStatement)


class ComprehensionBlock(Node):
    left = pyast.field(Identifier)
    right = pyast.field(Expression)
    each = pyast.field(bool)

### Statements


class BreakStatement(Statement):
    label = pyast.field(Identifier, null=True)


class ContinueStatement(Statement):
    label = pyast.field(Identifier, null=True)


class DebuggerStatement(Statement):
    pass


class DoWhileStatement(Statement):
    body = pyast.field(Statement)
    test = pyast.field(Expression)


class EmptyStatement(Statement):
    pass


class ExpressionStatement(Statement):
    expression = pyast.field(Expression)


class ForStatement(Statement):
    init = pyast.field((VariableDeclaration, Expression), null=True)
    test = pyast.field(Expression)
    update = pyast.field(Expression, null=True)
    body = pyast.field(Statement)


class ForInStatement(Statement):
    left = pyast.field((VariableDeclaration, Expression))
    right = pyast.field(Expression)
    body = pyast.field(Statement)
    each = pyast.field(bool, default=False)


class IfStatement(Statement):
    test = pyast.field(Expression)
    consequent = pyast.field(Statement)
    alternate = pyast.field(Statement, null=True)


class LabeledStatement(Statement):
    label = pyast.field(Identifier)
    body = pyast.field(Statement)


class LetStatement(Statement):
    head = pyast.seq(VariableDeclarator)
    body = pyast.field(Statement)


class ReturnStatement(Statement):
    argument = pyast.field(Expression, null=True)


class SwitchStatement(Statement):
    test = pyast.field(Expression)
    cases = pyast.seq(SwitchCase)
    lexical = pyast.field(bool, default=False)


class ThrowStatement(Statement):
    argument = pyast.field(Expression)


class TryStatement(Statement):
    block = pyast.field(BlockStatement)
    # JS API allows for single CatchClause here
    handler = pyast.seq(CatchClause, null=True)
    finalizer = pyast.field(BlockStatement, null=True)


class WhileStatement(Statement):
    test = pyast.field(Expression)
    body = pyast.field(Statement)


class WithStatement(Statement):
    object = pyast.field(Expression)
    body = pyast.field(Statement)

### Expressions


class ArrayExpression(Expression):
    elements = pyast.seq(Expression, null=True)


class AssignmentExpression(Expression):
    operator = pyast.field(AssignmentOperator)
    left = pyast.field(Expression)
    right = pyast.field(Expression)


class BinaryExpression(Expression):
    operator = pyast.field(BinaryOperator)
    left = pyast.field(Expression)
    right = pyast.field(Expression)


class CallExpression(Expression):
    callee = pyast.field(Expression)
    arguments = pyast.seq(Expression, null=True)


class ComprehensionExpression(Expression):
    body = pyast.field(Expression)
    blocks = pyast.seq(ComprehensionBlock)
    filter = pyast.field(Expression, null=True)


class ConditionalExpression(Expression):
    test = pyast.field(Expression)
    consequent = pyast.field(Expression)
    alternate = pyast.field(Expression)


class FunctionExpression(Function, Expression):
    pass


class GeneratorExpression(Expression):
    body = pyast.field(Expression)
    blocks = pyast.seq(ComprehensionBlock)
    filter = pyast.field(Expression, null=True)


class GraphExpression(Expression):
    index = pyast.field(int)
    expression = pyast.field(Literal)


class GraphIndexExpression(Expression):
    index = pyast.field(int)


class LetExpression(Expression):
    head = pyast.seq(VariableDeclarator)
    body = pyast.field(Expression)


class LogicalExpression(Expression):
    operator = pyast.field(LogicalOperator)
    left = pyast.field(Expression)
    right = pyast.field(Expression)


class MemberExpression(Expression):
    obj = pyast.field(Expression)
    prop = pyast.field((Identifier, Expression))
    computed = pyast.field(bool)


class NewExpression(Expression):
    callee = pyast.field(Expression)
    arguments = pyast.seq(Expression, null=True)


class ObjectExpression(Expression):
    properties = pyast.seq(Property, null=True)


class SequenceExpression(Expression):
    expressions = pyast.seq(Expression)


class ThisExpression(Expression):
    pass


class UnaryExpression(Expression):
    operator = pyast.field(UnaryOperator)
    argument = pyast.field(Expression)
    prefix = pyast.field(bool, default=False)


class UpdateExpression(Expression):
    operator = pyast.field(UpdateOperator)
    argument = pyast.field(Expression)
    prefix = pyast.field(bool)


class YieldExpression(Expression):
    argument = pyast.field(Expression, null=True)

### Patterns


class ArrayPattern(Pattern):
    elements = pyast.seq(Identifier, null=True)


class ObjectPattern(Pattern):
    properties = pyast.seq(Property, null=True)

### Literals

LET = "let"
VAR = "var"
CONST = "const"
NULL = "null"
