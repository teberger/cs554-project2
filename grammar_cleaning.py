
from cfg import Grammar


def nullable(grammar):
    '''
    Returns a list of the all non-terminals that are nullable
    in the given grammar
    '''
    
    nullable = set()
    productions = grammar.productions

    cardinality = -1
    while cardinality < len(nullable):
        cardinality = len(nullable)

        for non_term in productions:
            #if epsilon is in the rhs already,
            #the production is nullable
            if [] in productions[non_term]:
                nullable.add(non_term)
            else:
                isNullable = False
                for N in productions[non_term]:
                    #check to see if this specific production is
                    # nullable by checking to see if the join set of
                    # all symbols in the production are nullable.
                    # If they are not, that production is not nullable
                    isProductionNullable = True
                    for symbol in N:
                        isProductionNullable &= symbol in nullable
                    # This is the disjoint set of all nullable
                    # productions the correspond to this lhs
                    isNullable |= isProductionNullable

                # if any of the disjoint productions are nullable, 
                # then this is true. Therefore, add this production's
                # lhs to the nullable set
                if isNullable:
                    nullable.add(non_term)

    return nullable

def first(grammar):
    productions = grammar.productions
    #define the nullables
    nullable_non_terms = nullable(grammar)
    
    #initially set our table to the empty set of terminals
    prev_table = {non_term : set() for non_term in grammar.nonTerminals}
    #add just the productions of the form: 
    #   non_terminal -> terminal
    #to start the algorithm off
    for non_term in grammar.nonTerminals:
        for N in productions[non_term]:
            if [] == N: continue
            if N[0] not in grammar.nonTerminals:
                prev_table[non_term].add(N[0])

    has_changed = True

    while has_changed:
        has_changed = False
        #construct the new table so we don't interfere with the
        #previous one by adding things we wouldn't add this iteration
        new_table = prev_table.copy()

        for non_term in grammar.nonTerminals:
            for rhs in productions[non_term]:
                # if we have an epsilon, ignore it. It is the
                # equivalent of adding the empty set.
                if [] == rhs or rhs[0] not in grammar.nonTerminals:
                    continue

                first = rhs[0]
                # Now, we need to check to see if adding anything from
                # the first item in the rhs changes the current set of
                # terminals we have for this non_term

                # this is done by seeing if the rhs's first
                # non-terminal's first set can add anything to the
                # current set of terminals for non_term
                if len(prev_table[first] - prev_table[non_term]) > 0:
                    new_additions = prev_table[first] - prev_table[non_term]
                    #skip past all the nullables until we hit the end
                    #or we find a non-terminal. Add all the first sets
                    #for the next item in the production as we come
                    #across them
                    i = 1
                    while i+1 < len(rhs) and rhs[i] in nullable_non_terms:
                        if rhs[i + 1] in grammar.nonTerminals:
                            new_additions |= prev_table[rhs[i + 1]]
                        else:
                            #must list-ify to match the rest in the
                            #set
                            new_additions |= set([rhs[i+1]])
                            break
                        i += 1

                    new_table[non_term] |= new_additions
                    has_changed = True

        prev_table = new_table.copy()

    return prev_table
    
if __name__ == '__main__':
    x = Grammar('./testdata/html.txt')
    first_dict = first(x)
    for i in first_dict:
        print i, ':', first_dict[i]
    
