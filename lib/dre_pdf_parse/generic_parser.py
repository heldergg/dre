# -*- coding: utf-8 -*-

'''
Tokenizer, lexer and parser - generic documents
'''

##
# Imports
##

import re
from simple_parser import SimpleParser

##
# Parser configuration
##

# Text massager configuration

pre_massage_rules = (
    (r'Decreto - Lei', 'Decreto-Lei'),
    (ur' -', u'-'),
    (ur'- ', u'-'),
    (ur'—', '-'),
    (ur'DL nº', u'Decreto-Lei n.º'),
    )

post_massage_rules = (
    (r' ;', ';'),
    )

# Tokenizer configuration
t_is_header = re.compile(r'^(?:\d{1,2}|\d{1,2}\.\d{1,2})\s-\s.*$')
t_is_list = re.compile(r'^(?:(?:[A-Z](?:\d+)?|\d+|[a-z0-9]+\.\d+)\s*-|[a-z]+\))\s+.*$')

is_header = lambda t: bool(t_is_header.match(t))
is_upper = lambda t: t[:t.find(':')].isupper()
any_str = lambda t: True
is_semicolon = lambda t: t == ';'
asks_for_continuation = lambda t: t and t[-1] in ','
is_continuation = lambda t: t and t[0].islower() and not t_is_list.match(t)

tokenizer_rules = {
    'split_rules': r'(?:\n|(;))',
    'merge_rules': [
        (is_header, is_upper),
        (asks_for_continuation, any_str),
        (any_str, is_semicolon),
        (any_str, is_continuation),
        ],
    }

# Lexer configuration
t_ListItem01 = re.compile(r'^(?:[A-Z](?:\d+)?|\d|[a-z]\.\d)\s*-\s+.+$')
t_ListItem02 = re.compile(r'^[a-z]\)\s+.+$')
t_Article = re.compile(ur'Artigo \d+\.º(?:-[A-Z])?')
t_Paragraph = re.compile(r'^.*$')

lexicon = (
    (None, lambda t: not t),
    ('ListItem', lambda t: t_ListItem01.match(t)),
    ('ListItem', lambda t: t_ListItem02.match(t)),
    ('Article', lambda t: t_Article.match(t)),
    ('Paragraph', lambda t: t_Paragraph.match(t)),
    )

# Parser configuration
parser_rules = {
    'ListItem': '<p class="list_item">%s</p>',
    'Article': '<h5>%s</h4>',
    'Paragraph': '<p>%s</p>',
    }

parse_generic_document = SimpleParser(
    pre_massage_rules,
    tokenizer_rules,
    lexicon,
    parser_rules,
    post_massage_rules)
