# graphviz - create dot, save, render, view

"""Assemble DOT source code and render it with Graphviz.

>>> import graphviz
>>> dot = graphviz.Digraph(comment='The Round Table')

>>> dot.node('A', 'King Arthur')
>>> dot.node('B', 'Sir Bedevere the Wise')
>>> dot.node('L', 'Sir Lancelot the Brave')

>>> dot.edges(['AB', 'AL'])

>>> dot.edge('B', 'L', constraint='false')

>>> print(dot)  #doctest: +NORMALIZE_WHITESPACE
// The Round Table
digraph {
    A [label="King Arthur"]
    B [label="Sir Bedevere the Wise"]
    L [label="Sir Lancelot the Brave"]
    A -> B
    A -> L
    B -> L [constraint=false]
}
"""

from .backend import (render, pipe, pipe_string, pipe_lines, pipe_lines_string,
                      unflatten, version, view,
                      ENGINES, FORMATS, RENDERERS, FORMATTERS,
                      ExecutableNotFound, RequiredArgumentError)
from .dot import Graph, Digraph
from .sources import Source
from .lang import escape, nohtml

__all__ = ['Graph', 'Digraph',
           'Source',
           'escape', 'nohtml',
           'render', 'pipe', 'pipe_string', 'pipe_lines', 'pipe_lines_string',
           'unflatten', 'version', 'view',
           'ENGINES', 'FORMATS', 'RENDERERS', 'FORMATTERS',
           'RequiredArgumentError', 'ExecutableNotFound',
           'set_default_engine', 'set_default_format']

__title__ = 'graphviz'
__version__ = '0.18.dev0'
__author__ = 'Sebastian Bank <sebastian.bank@uni-leipzig.de>'
__license__ = 'MIT, see LICENSE.txt'
__copyright__ = 'Copyright (c) 2013-2021 Sebastian Bank'

#: :class:`set` of known layout commands used for rendering
#:      (``'dot'``, ``'neato'``, ...)
ENGINES = ENGINES

#: :class:`set` of known output formats for rendering
#:      (``'pdf'``, ``'png'``, ...)
FORMATS = FORMATS

#: :class:`set` of known output formatters for rendering
#:      (``'cairo'``, ``'gd'``, ...)
FORMATTERS = FORMATTERS

#: :class:`set` of known output renderers for rendering
#:      (``'cairo'``, ``'gd'``, ...)
RENDERERS = RENDERERS

ExecutableNotFound = ExecutableNotFound

RequiredArgumentError = RequiredArgumentError


def set_default_engine(engine):
    if engine not in ENGINES:
        raise ValueError(f'unknown engine: {engine!r}')

    from .backend import Graphviz

    old_default_engine = Graphviz._engine
    Graphviz._engine = engine
    return old_default_engine


def set_default_format(format):
    if format not in FORMATS:
        raise ValueError(f'unknown format: {format!r}')

    from .backend import Graphviz

    old_default_format = Graphviz._format
    Graphviz._format = format
    return old_default_format
