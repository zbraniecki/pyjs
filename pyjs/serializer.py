import pyjs.ast
import sys

if sys.version >= "3":
    basestring = str

def is_string(string):
    return isinstance(string, basestring)


import re

precedence = {
        "||": 5,
        "&&": 6,
        "|": 7,
        "^": 8,
        "&": 9,
        "==": 10,
        "!=": 10,
        "===": 10,
        "!==": 10,
        "<": 11,
        "<=": 11,
        ">": 11,
        ">=": 11,
        "in": 11,
        "instanceof": 11,
        "<<": 12,
        ">>": 12,
        ">>>": 12,
        "+": 13,
        "-": 13,
        "*": 14,
        "/": 14,
        "%": 14,
}


class Serializer(object):
    @classmethod
    def is_bad_identifier(cls, e):
        return isinstance(e, pyjs.ast.Identifier) and not re.match(r'^[_$A-Za-z][_$A-Za-z0-9]*$', e.name)
                
    @classmethod
    def dump_for_head(cls, e, indent):
        lhs = None
        if isinstance(e.left, pyjs.ast.VariableDeclaration):
            lhs = "%s %s" % (e.left.string,
                             cls.dump_declarators(e.left.declarations, indent, True))
        else:
            lhs = cls.dump_expr(e.left, indent, 0, True)
        return "for %s(%s in %s)" % ("each " if e.each else "",
                                     lhs,
                                     cls.dump_expr(e.right, indent, 0, False))

    @classmethod
    def wrap_expr(cls, s, cprec, xprec):
        return s if (xprec > cprec) else "(%s)"

    @classmethod
    def dump_program(cls, prog):
        lines = [cls.dump_stmt(elem) for elem in prog.body]
        return '\n'.join(lines)

    @classmethod
    def dump_stmt(cls, e, indent=0):
        string = ''
        if isinstance(e, pyjs.ast.BlockStatement):
            string = "%s{\n%s%s}\n" % (" "*indent,
                                      "".join([cls.dump_stmt(x, indent+4) for x in e.body]),
                                      " "*indent)
        elif isinstance(e, pyjs.ast.VariableDeclaration):
            string = "%s%s %s;\n" % (" "*indent,
                                  e.kind,
                                  cls.dump_declarators(e.declarations,
                                                       indent,
                                                       False))
        elif isinstance(e, pyjs.ast.ExpressionStatement):
            s = cls.dump_expr(e.expression, indent, 0, False)
            if s.startswith(('function', 'let', '{')):
                s = "(%s)" % s
            return "%s%s;\n" % (" "*indent, s)
        elif isinstance(e, pyjs.ast.IfStatement):
            gotElse = e.alternate
            string = "%sif (%s)%s" % (" "*indent,
                                 cls.dump_expr(e.test, indent, 0, False),
                                 cls.dump_substmt(e.consequent, indent, gotElse))
            if gotElse:
                string = "%selse%s" % (string,
                                  cls.dump_substmt(e.alternate, indent))
        elif isinstance(e, pyjs.ast.ForInStatement):
            return "%s%s%s" % (" "*indent,
                               cls.dump_for_head(e, indent),
                               cls.dump_stmt(e.body, indent))
        elif isinstance(e, pyjs.ast.ReturnStatement):
            return "%sreturn%s;\n" % (" "*indent,
                                      " "+cls.dump_expr(e.argument, indent, 0, False) if e.argument else "")
        elif isinstance(e, pyjs.ast.FunctionDeclaration):
            string = '%s%s%s' % (" "*indent,
                                 cls.dump_funcdecl("function", e.id, e, indent),
                                 ";\n" if e.expression else "\n")
        else:
            print(e)
            print(type(e))
        return string

    @classmethod
    def dump_funcdecl(cls, init, id, e, indent=0):
        name = "" if id == None else cls.dump_expr(id, '####', 18, False)
        body=None
        if e.expression:
            body = cls.dump_expr(e.body, indent, 2, False)
            if body.startswith('{'):
                body = "(%s)" % body
            else:
                body = " %s" % body
        else:
            body = cls.dump_substmt(e.body, indent).rstrip()
        return "%s %s%s%s" % (init,
                              name,
                              cls.dump_params(e.params, indent),
                              body)

    @classmethod
    def dump_expr(cls, e, indent, cprec, noIn):
        if isinstance(e, pyjs.ast.ArrayExpression):
            return "[%s]" % ",".join([cls.dump_expr(i, indent, 2, False) for i in e.elements])
        elif isinstance(e, pyjs.ast.ObjectExpression):
            p = e.properties
            s = []
            for i in range(0, len(p)):
                prop = p[i]
                if prop.kind == "init":
                    s.append("%s: %s" % (cls.dump_expr(prop.key, indent, 18, False),
                                       cls.dump_expr(prop.value, indent, 2, False)))
                elif prop.kind in ("get", "set"):
                    s.append(cls.dump_funcdecl(prop.kind, prop.key, prop.value, indent))
                else:
                    s.append(cls.dump_unexpected(prop))
            return "{%s}" % ", ".join(s)
        elif isinstance(e, pyjs.ast.LetExpression):
            return cls.wrap_expr("let (%s) %s" % (
                                     cls.dump_declarators(e.head, indent, False),
                                     cls.dump_expr(e.body, indent, 2, False)
                                 ),
                                 cprec,
                                 3)
        elif isinstance(e, pyjs.ast.ConditionalExpression):
            return cls.wrap_expr("%s?%s:%s" % (
                                     cls.dump_expr(e.test, indent, 4, noIn),
                                     cls.dump_expr(e.consequent, indent, 0, noIn),
                                     cls.dump_expr(e.alternate, indent, 3, noIn)
                                 ),
                                 cprec,
                                 4)
        elif isinstance(e, pyjs.ast.Identifier):
            return e.name
        elif isinstance(e, pyjs.ast.Literal):
            if is_string(e.value):
                return "\"%s\"" % e.value
            elif type(e.value) is int:
                return str(e.value)
            elif issubclass(e.value, pyjs.ast.Literal):
                return e.value.string
        elif isinstance(e, pyjs.ast.CallExpression):
            callee = cls.dump_expr(e.callee, indent, 17, False)
            args = cls.dump_args(e.arguments, indent)
            return cls.wrap_expr("%s%s" % (callee, args),
                                 cprec,
                                 18)
        elif isinstance(e, pyjs.ast.NewExpression):
            if len(e.arguments) == 0:
                string = "new %s" % cls.dump_expr(e.callee, indent, 18, False)
            else:
                string = "new %s%s" % (cls.dump_expr(e.callee, indent, 18, False),
                                       cls.dump_args(e.arguments, indent))
            return cls.wrap_expr(string, cprec, 17)
        elif isinstance(e, pyjs.ast.ThisExpression):
            return "this"
        elif isinstance(e, pyjs.ast.MemberExpression):
            obj = cls.dump_expr(e.obj, indent, 17, False)
            if e.computed:
                prop = "[%s]" % cls.dump_expr(e.prop, indent, 0, False)
            else:
                if cls.is_bad_identifier(e.prop):
                    prop = "[%s]" % cls.uneval(e.prop.name)
                else:
                    prop = ".%s" % cls.dump_expr(e.prop, indent, 18, False)
            return cls.wrap_expr("%s%s" % (obj, prop), cprec, 18)
        elif isinstance(e, pyjs.ast.UnaryExpression):
            op = e.operator.token
            if op in ('typeof', 'void', 'delete'):
                op = '%s ' % op
            s = cls.dump_expr(e.argument, indent, 15, False)
            return cls.wrap_expr('%s%s' % ((op, s) if e.prefix else (s, op)),
                                 cprec,
                                 15)
        elif isinstance(e, pyjs.ast.BinaryExpression):
            if e.operator.token == "..":
                pass
            else:
                op = e.operator.token
                prec = precedence[op]
                parens = (op == "in" and noIn) or cprec >= prec
                if parens:
                    noIn = False
                a = [cls.dump_expr(e.right, indent, prec, (noIn and prec <= 11)), op]
                x = e.left
                while type(x) == type(e) and precedence[x.operator] == prec:
                    a.append(cls.dump_expr(x.right, indent, prec, (noIn and prec <= 11)))
                    a.append(x.operator)
                    x = x.left
                a.append(cls.dump_expr(x, indent, prec-1, (noIn and prec -1 <= 11)))
                a.reverse()
                s = ' '.join(a)
                return '(%s)' % s if parens else s
        elif isinstance(e, pyjs.ast.AssignmentExpression):
            left = cls.dump_expr(e.left, indent, 3, noIn)
            right = cls.dump_expr(e.right, indent, 2, noIn)
            return cls.wrap_expr("%s %s %s" % (left, e.operator.token, right),
                                 cprec,
                                 3)
        elif isinstance(e, pyjs.ast.FunctionExpression):
            return cls.wrap_expr(
                cls.dump_funcdecl("function", e.id, e, indent),
                cprec,
                3 if e.expression else 19)
        else:
            raise Exception()


    @classmethod
    def dump_substmt(cls, e, indent, more=False):
        if isinstance(e, pyjs.ast.BlockStatement):
            body = cls.dump_stmt(e, indent)
            if more:
                body = "%s " % body[indent:len(body)-1]
            else:
                body = body[indent:]
            return " %s" % body
        return "\n%s%s" % (cls.dump_stmt(e, indent + 4),
                           " "*indent if more else "")


    @classmethod
    def dump_params(cls, arr, indent=0):
        return "(%s)" % ", ".join([cls.dump_expr(x, '####', 18, False) for x in arr])

    @classmethod
    def dump_args(cls, arr, indent=0):
        return "(%s)" % ", ".join([cls.dump_expr(x, indent, 2, False) for x in arr])

    @classmethod
    def dump_declarators(cls, arr, indent, noIn):
        s = []
        for i in range(0, len(arr)):
            n = arr[i]
            if isinstance(n, pyjs.ast.VariableDeclarator):
                patt = cls.dump_expr(n.id, '####', 3, False)
                if n.init is None:
                    s.append(patt)
                else:
                    s.append("%s = %s" % (patt,
                                          cls.dump_expr(n.init, indent, 2, noIn)))
        return ", ".join(s)

