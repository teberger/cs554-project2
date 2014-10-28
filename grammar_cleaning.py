
def nullable(grammar):
    '''
    Returns a list of the all non-terminals that are nullable
    in the given grammar
    '''
    
    nullable = set()
    productions = set(production for production in grammar.productions)

    cardinality = -1
    while cardinality < len(nullable):
        cardinality = len(nullable)
    
        for production in productions:
            #if epsilon is in the rhs already,
            #the production is nullable
            if '' in production.rhs:
                nullable.add(production.lhs)
            else:
                isNullable = False
                for N in production.rhs:
                    #check to see if this specific production is
                    # nullable by checking to see if the join set of
                    # all symbols in the production are nullable.
                    # If they are not, that production is not nullable
                    isProductionNullable = True
                    for symbol in N:
                        isProductionNullable = isProductionNullable 
                                               and symbol in nullable
                    # This is the disjoint set of all nullable
                    # productions the correspond to this lhs
                    isNullable = isProductionNullable or isNullable

                # if any of the disjoint productions are nullable, 
                # then this is true. Therefore, add this production's
                # lhs to the nullable set
                if isNullable:
                    nullable.add(production.lhs)

    return nullable
    
    
