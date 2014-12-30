# -*- coding: utf-8 -*-

'''This module creates graphs from a given document
and its connections
'''

##
## Imports
##

import pygraphviz as pgv

# Local Imports
from dreapp.models import Document, DocumentNext

# Consts

INLINK = 1
OUTLINK = 2
BOTH = 3


class DREGraph( object ):
    def __init__(self, document):
        self.graph = pgv.AGraph(strict=False,directed=True)
        self.document = document
        self.max_depth = 0
        self.filter_by_doc_type = [
            u'CARTA DE LEI',
            u'DECRETO LEI',
            u'LEI',
            u'LEI CONSTITUCIONAL',
            u'LEI ORGÂNICA',
            ]
        self.exclude_revoked = True
        self.direction = OUTLINK
        self.filter_by_doc_type = []

    def exclude(self, document):
        if self.exclude_revoked and not document.in_force:
            return True
        if document.doc_type not in self.filter_by_doc_type:
            return True
        return False

    def adct_vertexes(self, node):
        if self.direction == BOTH:
            link_generator = node.links
        elif self.direction == INLINK:
            link_generator = node.in_links
        elif self.direction == OUTLINK:
            link_generator = node.out_links
        for vertex in link_generator():
            yield vertex

    def get_node_list_bfs(self):
        '''
        Breadth-first search

        Here we make the graph transversal in order to get all the nodes from
        the graph. This might be an expensive operation for the larger graphs.
        '''

        queue = []
        document = self.document
        queue.append( document )
        vertexes = { document.id: document }
        edges = set()

        while queue:
            node = queue.pop()
            print "Queue: %d Vertexes: %d Edges: %d" % (len(queue), len(vertexes), len(edges))
            for adjacent_vertex in self.adct_vertexes(node):
                if adjacent_vertex.id not in vertexes:
                    if self.filter_by_doc_type and self.exclude(adjacent_vertex):
                        continue
                    vertexes[ adjacent_vertex.id ] = adjacent_vertex
                    queue.append( adjacent_vertex )
                    edges.add( ( adjacent_vertex, node ) )
        return vertexes, edges

    def adct_edges(self, node):
        if self.direction == BOTH:
            edge_generator = node.edges
        elif self.direction == INLINK:
            edge_generator = node.in_edges
        elif self.direction == OUTLINK:
            edge_generator = node.out_edges
        for edge in edge_generator():
            yield edge

    def get_node_list_dfs(self):
        '''
        Depth-first search

        Here we make the graph transversal in order to get all the nodes from
        the graph. Exloring depth first allow us to stop at a given depth
        (this is harder to do using a breadth first strategy). The problem is
        that a dfs strategy is recursive so we can't use it for large graphs.
        '''
        vertexes = {}
        edges = set()
        def dfs( vertex, depth=0 ):
            vertexes[vertex.id] = vertex
            for edge in self.adct_edges(vertex):
                print "Depth: %d Edges: %d Vertexes: %d" % (depth, len(edges), len(vertexes))
                if edge not in edges:
                    adjacent_vertex = edge[0] if vertex == edge[1] else edge[1]
                    if self.filter_by_doc_type and self.exclude(adjacent_vertex):
                        continue
                    if adjacent_vertex.id not in vertexes and depth+1 <= (self.max_depth-1):
                        dfs( adjacent_vertex, depth+1 )
                    edges.add(edge)

        dfs( self.document )
        return vertexes, edges

    def get_node_list(self):
        if self.max_depth:
            return self.get_node_list_dfs()
        else:
            return self.get_node_list_bfs()

    def svg(self):
        vertexes, edges = self.get_node_list()
        f = open("teste_from_%d-vertexes_%d-edges_%d-depth_%d-%s-%s.dot" % (
            self.document.id,
            len(vertexes),
            len(edges),
            self.max_depth,
            "in_force" if self.exclude_revoked else "all",
            ("in_links" if self.direction == INLINK else
             "out_links" if self.direction == OUTLINK else "both" )
            ),"w")
        f.write("digraph G {\n")
        for e in edges:
            f.write("%d -> %d;\n" % (e[0].id, e[1].id))
        f.write("}")
        f.close()



##
## Main
##

def main():
    print 'Nothing\'s done here'

if __name__ == '__main__':
    main()
