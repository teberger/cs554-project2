from parser import Parser
from cfg import Grammar
from llvm import *

def ast_to_cst(ast):
    pass

def cst_to_llvm(cst):
    pass

if __name__ == '__main__':
    g = Grammar('./testdata/html.txt')
    x = Parser(g)
