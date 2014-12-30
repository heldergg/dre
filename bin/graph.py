#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Graph generation from the document links.
'''

# Imports

import sys
import os.path
import argparse

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

# Local imports

from dreapp.models import Document
from dre_graph import DREGraph

##
# Graphs
##

def gen_graph( args ):
    document = Document.objects.get(id=312624)
    document = Document.objects.get(id=57579)
#    document = Document.objects.get(id=188600) # Lei constitucional
#    document = Document.objects.get(id=257685)
#    document = Document.objects.get(id=211216)
    graph = DREGraph( document )

    graph.svg()

##
# Command Line Parser
##

parser = argparse.ArgumentParser(description='DRE graph generation utility')
subparsers = parser.add_subparsers( title='Commands' )

# Available commands
parser_la = subparsers.add_parser(
        'graph',
        help='Creates a graph',
        description='Graph generation')
parser_la.set_defaults(func=gen_graph)


##
# Main
##

if __name__ == '__main__':
    args = parser.parse_args()
    args.func(args)

