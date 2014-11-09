#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Data structures for representing context-free grammars over ASCII alphabets
    and parsing functions to read grammar descriptions in files. The grammars
    are specified formally by:

    Grammar -> Grammar Production
    Grammar -> Production
    Production -> Symbol Arrow List
    List -> List Symbol
    List ->

    Where any symbols appearing left of the arrow are non-terminals, and the
    non-terminal of the first production is starting production. Productions are
    separated by lines.
"""

from pyparsing import *


# pyparsing definitions for above-specified context-free grammar.
pyp_Arrow = Keyword("->").suppress()
pyp_Symbol = Word(alphanums)
pyp_List = ZeroOrMore(~LineStart().leaveWhitespace() + Word(printables))
pyp_Production = Group(pyp_Symbol.setResultsName("lhs") +
                       pyp_Arrow.suppress() +
                       Group(pyp_List).setResultsName("rhs"))
pyp_Grammar = ZeroOrMore(pyp_Production)

EOF = '\0'
EPSILON = '`'

class Production:
    """ Represents a production. """

    def __init__(self, lhs, rhs):
        """
        :param str lhs: Left-hand-side symbol.
        :param list[str] rhs: List of right-hand-side symbols.
        """
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return str(self.lhs) + " -> " + str(self.rhs)

    def __repr__(self):
        return str(self)

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        return isinstance(other, Production)\
               and self.lhs == other.lhs\
               and self.rhs == other.rhs


class Grammar:
    """ Data structure for context-free grammar. """

    def __init__(self, grammar=None):

        self.productions = dict()
        self.nonTerminals = set()
        self.terminals = set()
        self.start = ""

        if grammar is not None:
            # Convert ParseResult objects into Productions.
            parse = pyp_Grammar.parseFile(grammar)
            productions = [Production(p.lhs, p.rhs.asList()) for p in parse]

            # First production's left-hand-side is start symbol.
            self.start = productions[0].lhs

            # Hygiene checks.
            productions = Generating(productions)
            if self.start not in set(p.lhs for p in productions):
                raise Exception("Starting production is non-generating!")
            productions = Reachable(productions, self.start)

            # Add all of the productions to the grammar.
            for production in productions:
                self.addProduction(production.lhs, production.rhs)

            # Determine set of terminals by finding set of all symbols, then
            # subtracting the intersection of all symbols with non-terminals.
            for righthandsides in self.productions.values():
                for rhs in righthandsides:
                    self.terminals |= set(rhs)

            self.terminals = self.terminals - self.nonTerminals

    def addProduction(self, lhs, rhs):
        """Adds a production to the grammar. If the production's LHS already
        exists in the dictionary, the RHS is appended to the value
        list. If the LHS is not in the dictionary, it is added, and
        the RHS is added as a list.

        :param str lhs: Left-hand-side of the production.
        :param list[str] rhs: Right-hand-side of the production.

        """
        if lhs in self.productions:
            self.productions[lhs].append(rhs)
        else:
            self.productions[lhs] = [rhs]

        self.nonTerminals.add(lhs)


def Generating(productions):
    """Returns a list of generating rules from a list of productions.

    This algorithm first identifies all initially-productive rules: -
    Rules with only terminals on the right-hand-side.  - Rules with
    the empty string (epsilon) on the right-hand-side.  Productions
    are then marked productive if their right-hand-side consists of
    only terminals and non-terminals marked as productive. This
    process is repeated until no new results are yielded. Any
    productions not marked as productive at this point are
    unproductive.

    :param list[Production] productions: List of productions to examine.
    :rtype: list[Production]

    """
    nonTerms = set(production.lhs for production in productions)
    productive = set()

    # Repeat until no new results are yielded.
    previousSize = -1
    while previousSize < len(productive):
        previousSize = len(productive)

        for production in productions:
            # Don't bother with productions that are already marked.
            if production.lhs not in productive:

                # Empty rhs is productive.
                if not production.rhs:
                    productive.add(production.lhs)

                # If every symbol in the RHS is productive, lhs is
                # productive.
                else:
                    isProductive = True
                    for symbol in production.rhs:
                        if symbol in nonTerms and symbol not in productive:
                            isProductive = False
                            break

                    if isProductive:
                        productive.add(production.lhs)

    # Build list of all productions with generating left-hand-sides,
    # but remove any that have non-generating variables in their
    # right-hand-side.x+y
    unproductive = nonTerms - productive
    return [p for p in productions if
            p.lhs in productive
            and set(p.rhs).isdisjoint(unproductive)]


def Reachable(productions, start):
    """
    Returns a list of reachable rules from a list of productions.

    This algorithm initially marks the start productions as reachable. For every
    reachable state, all non-terminals in the reachable states' right-hand-sides
    are then marked as reachable (with a bit of checking to make sure it doesn't
    repeatedly check the same rules). This process is repeated until no new
    reachable states are found.

    :param list[Production] productions: List of productions to examine.
    :param str start: The starting non-terminal.
    :rtype: list[Production]
    """
    nonTerms = set(production.lhs for production in productions)
    reachable = {start}
    marked = set(filter((lambda p: p.lhs == start), productions))
    unmarked = set(productions) - marked

    # Repeat until no new results are yielded.
    previousSize = -1
    while previousSize < len(reachable):
        previousSize = len(reachable)

        # Find all new reachable non-terminals in current marked set. Generate
        # a new marked set from all newly reachable non-terminals.
        nextMarked = set()
        for production in marked:
            for symbol in production.rhs:
                if symbol in nonTerms and symbol not in reachable:
                    nextMarked |= set(filter((lambda p: p.lhs == symbol), unmarked))
                    reachable.add(symbol)

        marked = nextMarked
        unmarked -= marked

    # Create new list of only reachable rules.
    return [p for p in productions if p.lhs in reachable]
