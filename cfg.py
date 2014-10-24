#!/usr/bin/env python

""" Data structures for representing context-free grammars over ASCII alphabets
    and parsing functions to read grammar descriptions in files. The grammars
    are specified formally by:

    Grammar -> Grammar Production
    Grammar -> Production
    Production -> Symbol Arrow List
    List -> List Symbol
    List ->

    Where symbols left of the arrow are non-terminal, symbols right of the arrow
    are terminal, and the non-terminal of the first production specified is the
    start symbol.
"""

from pyparsing import *


# pyparsing definitions for above-specified context-free grammar.
pyp_Arrow = Keyword("->").suppress()
pyp_Symbol = Word(alphanums, exact=1)
pyp_List = ZeroOrMore(pyp_Symbol)
pyp_Production = Group(pyp_Symbol + pyp_Arrow + pyp_List) + NewLine()
pyp_Grammar = ZeroOrMore(pyp_Production)


class Grammar:
    """ Data structure for context-free grammar. """

    def __init__(self):

        self.productions = dict()
        self.start = ""
        self.terminals = set()
        self.nonTerminals = set()

    def addProduction(self, lhs, rhs):
        """
        Adds a production to the grammar. Performs sanity checks first and
        records terminal/non-terminal symbols.

        :param str lhs: Left-hand-side of the production.
        :param str rhs: Right-hand-side of the production.
        """

        rhsSymbols = (symbol for symbol in rhs)

        # Sanity guards: throw an exception if already-established terminal
        # symbols are being added to non-terminals, or vice-versa.
        if lhs in self.terminals:
            raise Exception("Attempted to add production " +
                            "(" + lhs + " --> " + rhs + ") " +
                            "to grammar, but LHS symbol is terminal.")

        if not rhsSymbols.isdisjoint(self.nonTerminals):
            raise Exception("Attempted to add production " +
                            "(" + lhs + " --> " + rhs + ") " +
                            "to grammar, but RHS has non-terminals.")

        # Add production to the dictionary (or just append the rhs to an already
        # extant list), lhs to non-terminals, and rhs to terminals.
        if lhs in self.productions:
            self.productions[lhs].append(rhs)
        else:
            self.productions[lhs] = [rhs]

        self.nonTerminals.add(lhs)
        self.terminals |= rhsSymbols

if __name__ == "__main__":
    print pyp_Grammar.parseFile("testdata/simple.txt")