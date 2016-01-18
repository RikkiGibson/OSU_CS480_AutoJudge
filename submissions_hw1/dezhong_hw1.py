import sys
logs = sys.stderr
import compiler
from compiler.ast import *

__author__ = "Dezhong Deng (TA)"

class Translator():

    def __init__(self):
        self.memo = set()

    def generate_c(self, n):
        # print "generate_c:"+str(n)
        if isinstance(n, Module):
            main = self.generate_c(n.node)
            assign = "int "+", ".join(list(self.memo))+";"
            return "\n".join([
                "#include <stdio.h>",
                "",
                "int main()",
                "{",
                assign,
                main,
                "return 0;",
                "}"
            ])
        elif isinstance(n, Stmt):
            return "\n".join(map(self.generate_c, n.nodes))
        elif isinstance(n, Const):
            return str(n.value)
        elif isinstance(n, Name):
            return str(n.name)
        elif isinstance(n, AssName):
            var = str(n.name)
            if var not in self.memo:
                self.memo.add(var)            
            return var
        elif isinstance(n, Add):
            left = self.generate_c(n.left)
            right = self.generate_c(n.right)
            return left+" + "+right
        elif isinstance(n, UnarySub):
            return "(-"+self.generate_c(n.expr)+")"
        elif isinstance(n, Assign):
            var = self.generate_c(n.nodes[0])
            value = self.generate_c(n.expr)
            return var+" = "+value+";"
        elif isinstance(n, For):
            loopvar = self.generate_c(n.assign)
            looprange = self.generate_c(n.list.args[0])
            expr = self.generate_c(n.body)
            newvar = loopvar+"_"
            while (newvar in expr or newvar in looprange or newvar in self.memo):
                newvar += "_"
            newrange = "rng"
            while (newrange in expr or newrange in looprange or newrange in self.memo):
                newrange += "_"
            self.memo.add(newrange)
            return "\n".join([
                newrange+ " = "+looprange+";",
                "for ( int "+newvar+" = 0; "+newvar+" < "+newrange+"; "+newvar+" ++)",
                "{",
                loopvar+ " = "+newvar+";",
                expr,
                "}"
            ])
        elif isinstance(n, Printnl):
            left = " ".join(["%d"] * len(n.nodes))
            right = ", ".join(map(self.generate_c, n.nodes))
            return "printf(\""+left+"\\n\", "+right+");"
        else:
            raise sys.exit("Error in generate_c: unrecognized AST node: "+str(n))
    

if __name__ == "__main__":
    try:
        inputcode = "".join(sys.stdin.readlines())
        ast = compiler.parse(inputcode)
        # print "INPUTCODE:"
        # print inputcode
        # print "AST:"
        # print ast
        translator = Translator()
        outputcode = translator.generate_c(ast)
        # print "OUTPUTCODE:"
        print outputcode
        # fout = open("b.c", "w")
        # print >> fout, outputcode
        # fout.close()
    except Exception, e:
        print >> logs, e.args[0]
        exit(-1)
