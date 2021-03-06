from cfg import Grammar, EOF, EPSILON


def nullable(grammar):
    '''
    Returns a list of the all non-terminals that are nullable
    in the given grammar. A nullable non-terminal is calculated
    as a closure using the following rules:
      
      nullable(A -> Epsilon) -> True
      nullable(A -> a) -> False
      nullable(A -> AB) -> nullable(A) AND nullable(B)
      nullable(A -> A1 | A2 | ... | AN) -> nullable(A1) OR .. OR nullable(A_n)
    
    :param Grammar grammar: the set of productions to use and
                            wrapped in the Grammar object
    :return a set of all non-terminals that can be nullable
    '''
    
    nullable = set()
    productions = grammar.productions

    cardinality = -1
    while cardinality < len(nullable):
        cardinality = len(nullable)

        for non_term in productions:
            #if epsilon is in the rhs already,
            #the production is nullable
            if EPSILON in productions[non_term]:
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
    '''A first set calucation for a grammar returns a dictionary of all
    the first terminals that can proceed the rest of a parse given a
    non-termial symbol. First is a closure that is calculated as
    follows:
    
      first(Epsilon) -> EmptySet
      first(A -> a) -> { a } 
                        
      first(A -> A B) -> { first(A) U first( B),   if nullable(A)
                        { first(A),              otherwise
      first(A -> A1 | A2 | ... | AN) -> first(A1) U first(A2 U ... U first(AN)

    :param Grammar grammar: the set of productions to use wrapped in a 
                            Grammar object
    :return dict{Non-Terminal : set(Terminal)}: a table of all terminals that
                                                could come from a given
                                                non-terminal
    '''
    productions = grammar.productions
    #define the nullables
    nullable_non_terms = nullable(grammar)
    
    #initially set our table to the empty set of terminals
    prev_table = {non_term : set() for non_term in grammar.nonTerminals}
    #add just the productions of the form: 
    #   non_terminal -> terminal
    #to start the algorithm off
    for non_term in grammar.nonTerminals:
        for rhs in productions[non_term]:
            if [] == rhs: continue
            if rhs[0] in grammar.terminals or rhs[0] == EPSILON:
                prev_table[non_term].add(rhs[0])

    has_changed = True

    while has_changed:
        has_changed = False
        #construct the new table so we don't interfere with the
        #previous one by adding things we wouldn't add this iteration
        new_table = prev_table.copy()

        for non_term in grammar.nonTerminals:
            for rhs in productions[non_term]:
                # if we have an epsilon, add it to the first set of this
                if len(rhs) == 0:
                    if EPSILON not in prev_table[non_term]:
                        has_changed = True
                        new_table[non_term] |= set([EPSILON])
                    continue

                # we already handled this above
                if rhs[0] in grammar.terminals or rhs[0] == EPSILON:
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
    
def create_first_from_list(first_table, nullables, symbol_list):
    if len(symbol_list) == 0: return set([EPSILON])

    #if it starts with a terminal, return the singleton set
    if symbol_list[0] not in first_table.keys():
        return set([symbol_list[0]])

    first_set = set().union(first_table[symbol_list[0]])
    if symbol_list[0] in nullables:
        recursive_set = create_first_from_list(first_table, nullables, symbol_list[1:])
        first_set.union(recursive_set)

    return first_set

def betas_following(non_terminal, productions):
    ret_set = {}

    for lhs,all_rhs in productions.iteritems():
        for rhs in all_rhs:
            if non_terminal in rhs:
                symbol_list = rhs
                while non_terminal in symbol_list:
                    idx = symbol_list.index(non_terminal)
                    beta = []

                    if idx < len(symbol_list):
                        beta = symbol_list[idx + 1:]

                        if lhs in ret_set:
                            ret_set[lhs].append(beta)
                        else:
                            ret_set[lhs] = [beta]
                    
                    symbol_list = beta
    return ret_set

def follows(grammar):
    '''Calculates all terminals that can follow a given non terminal.
    Follows is a closure calculated by the following rules:
    
      given [M -> ANB] -> follows(N) = follows(N) U first(B)
                          if nullable(B) then
                            follows(M) = follows(M) U follows(N)
      given [M -> A N B1...A N B2...A N BX]
                   -> follows(N) = first(B1) U first(B2) U ... 
                                      U first(BX)
                                   if nullable(B_i) then
                                     follows(M) = follows(M) U follows(N)
    
    :param Grammar grammar: the set of productions to use as a Grammar
                            object
    :return dict{non-Terminal : set(terminals)}: the set of terminal characters
                                                 that can follow any given
                                                 non-terminal
    '''

    first_table = first(grammar)
    nullable_set = nullable(grammar)
    follows_table = {non_term : set() for non_term in grammar.nonTerminals}

    #add EOF to the follows set for the start of the follows table
    follows_table[grammar.start] |= set([EOF])

    #iterate until there are no changes. Construct the closure.
    changed = True
    while changed:
        changed = False

        # We need to construct the follows table for each non-terminal
        for non_terminal in grammar.nonTerminals:
            #Get all productions of the form X -> a A beta
            beta_productions = betas_following(non_terminal, grammar.productions)

            #Iterate over all productions of the previous form. LHS refers to X
            for lhs in beta_productions:
                #This is for each specific 'beta' that could be of the form X -> a A beta
                for beta in beta_productions[lhs]:
                    # if there are no productions following 'A', then do this..
                    if beta == []:
                        #Add Follows(X) to Follows(A)
                        for elem in follows_table[lhs]:
                            if elem not in follows_table[non_terminal]:
                                changed = True
                                follows_table[non_terminal].add(elem)
                        continue

                    #Construct First(beta)
                    first_of_beta = create_first_from_list(first_table, nullable_set, beta)

                    #Add all elements in First(beta) to Follows(A)
                    for elem in (first_of_beta - set([EPSILON])):
                        if elem not in follows_table[non_terminal]:
                            changed = True
                            follows_table[non_terminal].add(elem)

                    #If 'beta' is nullable, then do this...
                    if EPSILON in first_of_beta:
                        #Add each element in Follows(X) to Follows(A)
                        for elem in follows_table[lhs]:
                            if elem not in follows_table[non_terminal]:
                                changed = True
                                follows_table[non_terminal].add(elem)

    return follows_table
