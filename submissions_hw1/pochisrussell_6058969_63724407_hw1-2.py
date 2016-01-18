#!/usr/bin/env python2


import compiler
import uuid
from operator import add
from sys import stdin, stdout



def a(*xss):
    return next(iter(
        reduce(add, (x.vars() for x in xs))
        for xs in xss
    ))


def tempname():
    return "temp_" + uuid.uuid4().get_hex()


compiler.ast.Module.to_c = lambda self: (
    "#include <stdio.h>\nint main()\n{\n" +
    "int " + ", ".join(var for var in set(self.node.vars())) + ";\n" +
    self.node.to_c() + "}\n"
)

compiler.ast.Stmt.vars = lambda self: a(self.nodes)
compiler.ast.Stmt.to_c = lambda self: (
    "".join(n.to_c() + ";\n" for n in self.nodes)
)

compiler.ast.Assign.vars = lambda self: a(self.nodes) + self.expr.vars()
compiler.ast.Assign.to_c = lambda self: (
    self.nodes[0].to_c() + " = " + self.expr.to_c()
)

compiler.ast.Printnl.vars = lambda self: []
compiler.ast.Printnl.to_c = lambda self: (
    "printf(\"" + " ".join("%d" for _ in self.nodes) + "\\n\", " +
    ", ".join(n.to_c() for n in self.nodes) +
    ")"
)

compiler.ast.For.vars = lambda self: self.body.vars() + self.assign.vars()
def For__to_c(self):
    if isinstance(self.list, compiler.ast.CallFunc) and \
            self.list.node.name == "range":
        return (
            "{{\n"
            "int {m2} = {m};\n"
            "for (int {i2} = 0; {i2} < {m2}; ++{i2}) {{\n"
            "{i} = {i2};\n"
            "{b}"
            "}}\n"
            "}}\n"
            .format(
                i=self.assign.name,
                i2=tempname(),
                m=self.list.args[0].to_c(),
                m2=tempname(),
                b=self.body.to_c(),
            )
        )
    else:
        raise Exception("Not implemented")
compiler.ast.For.to_c = For__to_c

compiler.ast.AssName.vars = lambda self: [self.name]
compiler.ast.AssName.to_c = lambda self: self.name

compiler.ast.Add.vars = lambda self: []
compiler.ast.Add.to_c = lambda self: (
    self.left.to_c() + " + " + self.right.to_c()
)

compiler.ast.Compare.vars = lambda self: []
compiler.ast.Compare.to_c = lambda self: (
    self.expr.to_c() +  # left
    " " + self.ops[0][0] +  # operator
    " " + self.ops[0][1].to_c()  # right
)

compiler.ast.UnarySub.vars = lambda self: []
compiler.ast.UnarySub.to_c = lambda self: (
    "(-(" + self.expr.to_c() + "))"
)

compiler.ast.Const.vars = lambda self: []
compiler.ast.Const.to_c = lambda self: (
    ("(" + str(self.value) + ")") if self.value < 0 else str(self.value)
)

compiler.ast.Name.vars = lambda self: []
compiler.ast.Name.to_c = lambda self: (
    self.name
)


t = compiler.parse(stdin.read())
stdout.write(t.to_c())
