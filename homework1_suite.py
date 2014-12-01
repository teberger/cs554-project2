import re
from cfg import Grammar
from ast_parser import Parser
import ast_to_llvm
import ast_reductions
import subprocess
import sys

var = ('var','[a-zA-Z]+')
num = ('num','[1-9]{1}[0-9]?')
eq = (':=',':=')
semi = (';', ';')
skip = ('skip', 'skip')
if_keyword = ('if', 'if')
fi_keyword = ('fi', 'fi')
then_keyword = ('then', 'then')
else_keyword = ('else', 'else')
do_keyword = ('do','do')
od_keyword = ('od', 'od')
while_keyword = ('while', 'while')
open_paren = ('(', '\(')
close_paren = (')', '\)')
relop = ('relop', '<=|>=|!=|=|<|>')
bop = ('bop', '&&|\|\|')
true = ('true', 'true')
false = ('false', 'false')

terminals = {c : re.compile(v) for c,v in [eq, semi, skip, if_keyword, fi_keyword, then_keyword, else_keyword, do_keyword, od_keyword, while_keyword, open_paren, close_paren, relop, bop, true, false, var, num]}

def tokenize(string):
    string = re.sub('\s', ',', string)
    tokens = string.split(',')

    pairs = []
    for token in tokens:
        for term in terminals:
            #the first one that matches gets precedence
            m = re.search(terminals[term], token)
            if m:
                pairs.append((term, token))
                continue
    return pairs

def compile_to_llvm(file):
    print("Opening file....")
    string = open(file,'r').read()
    print('Done.')

    print('Lexing...')
    tokens = tokenize(string)
    print('Done.')
    
    print('Constructing parser...')
    parser = Parser(Grammar('./testdata/homework1_grammar.txt'))
    print('Done.')
    
    print('Parsing tokens...')
    root = parser.ll1_parse(tokens)
    print('Done.')

    print('Reducing AST...')
    root = ast_reductions.reduce_ast(root)
    print('Done.')

    print('Constructing CST...')
    cst = ast_to_llvm.ast_to_cst(root)
    print('Done.')

    print('Constructing LLVM code...')
    llvm_code = ast_to_llvm.reduce_cst_to_llvm(cst)
    llvm_code.verify()
    print('Done.')

    print 
    print
    print('****LLVM Code:*****')
    print llvm_code
    print

    return llvm_code


def llvm_to_native(name, llvm):
    print('Constructing native code...')
    obj = name + '.o'
    dst = name

    print("* Compiling to `{}'.".format(dst))
    
    with open(obj, 'wb') as f:
        llvm.to_native_object(f)
    
    cmd = ['cc', '-o', dst, obj]
    r = subprocess.call(cmd)
    if r != 0:
        raise Exception("Failed to link with " + str(cmd))
    
    print('Done.')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print "Script file takes the file to parse, exiting..."
        exit(1)

    file_name = sys.argv[1]
    llvm_code = compile_to_llvm(file_name)
    llvm_to_native(file_name, llvm_code)
