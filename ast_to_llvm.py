from parser import Parser
from cfg import Grammar
from llvm import *
from ll1_tools import (first,follows)

def ast_to_llvm(ast):
    '''
    This function creates LLVM code for the toy language
    defined in ./testdata/homework1_grammar.txt
    
    It assumes the parser has the general structure of
    a AST wrt the Arithmetic language in the aforementioned
    grammar

    :param ast: a RoseTree that represents the AST of 
                the parsed Arithmetic language
    :return: LLVM code that would compile into a linux x86 
             executable
    '''

    
    pass

if __name__ == '__main__':
    g = Grammar('./testdata/homework1_grammar.txt')
    x = Parser(g)
    
    for c in follows(g):
        print c, ' -> ', follows(g)[c]
    

    x.ll1_parse([('while', 'while'), 
                 ('not', 'not'), 
                 ('true','true'), 
                 ('do','do'), 
                 ('var', 'x'),
                 ('aop', '+'),
                 ('num','123'),
                 ('od', 'od')
                ])
    
