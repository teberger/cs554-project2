from cfg import *
#from grammar_cleaning import nullable

def nullable(grammar):
    nullable_table = set();
    non_terminal = grammar.nonTerminals
    productions = grammar.productions
    modified = True
    while modified:
        modified = False
        for p in productions:
            if p not in nullable_table:
                for rhs in productions[p]:
                    if(rhs == []):
                        if(p not in nullable_table):
                            nullable_table.add(p)
                            modified = True
                    else:
                        is_nullable = True
                        for element in rhs:
                            if(element not in nullable_table): is_nullable = False
                        if is_nullable:
                            nullable_table.add(p)
                            modified = True
    return nullable_table

def first(grammar):
    nullable_set = nullable(grammar)
    first_table = {}
    non_terminal = grammar.nonTerminals
    for x in non_terminal:
        first_table[x] = set()
    productions = grammar.productions
    modified = True
    while modified:
        modified = False
        for p in productions:
            for rhs in productions[p]:
                if(rhs == []):
                    if('' not in first_table[p]):
                        first_table[p].add('')
                        modified = True
                elif(rhs[0] not in non_terminal):
                    if(rhs[0] not in first_table[p]):
                        first_table[p].add(rhs[0])
                        modified = True
                elif(rhs[0] not in nullable_set):
                    if(first_table[p] != first_table[rhs[0]]):
                        first_table[p].clear()
                        first_table[p] = first_table[rhs[0]].copy()
                        modified = True
                else:
                    new_set = set()
                    new_set = first_table[rhs[0]].copy()
                    #new_set.remove([])
                    if(len(rhs) > 1):
                        if(rhs[1] not in non_terminal): new_set.add(rhs[1])
                        else: new_set.union(first_table[rhs[1]])
                    if(new_set != first_table[p]):
                        first_table[p].clear()
                        first_table[p] = new_set.copy()
                        modified = True

    return first_table

x = Grammar('./testdata/test.txt')

print x.productions
print "=========================="
'''
print x.nonTerminals
print "=========================="
print x.start
'''

print nullable(x)
print first(x)

