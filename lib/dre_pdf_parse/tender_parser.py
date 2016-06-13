# -*- coding: utf-8 -*-

'''
Tokenizer, lexer and parser - tender documents
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
    (ur'DL nº', u'Decreto-Lei n.º'),
    )

post_massage_rules = (
    (r' ;', ';'),
    )

# Tokenizer configuration
t_is_header = re.compile(r'^(?:\d{1,2}|\d{1,2}\.\d{1,2})\s-\s.*$')
t_is_list = re.compile(r'^(?:[A-Z](?:\d+)?|\d+|[a-z0-9]+\.\d+)\s*-\s+.*$')

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
t_Ignore = re.compile(
    ur'(?ui)^Diário\s+da\s+República,\s+2\.ª\s+série\s+-\s+N\.º\s+\d+\s+-'
    ur'\s+\d+\s+de\s+[a-zç]+\s+de\s+\d{4}\s+-\s+'
    ur'(?:Anúncio\s+de\s+procedimento|'
    ur'Anúncio\s+de\s+concurso\s+urgente|'
    ur'Declaração\s+de\s+retificação\s+de\s+anúncio|'
    ur'Aviso\s+de\s+prorrogação\s+de\s+prazo)\s+'
    ur'n\.º\s+\d+/\d{4}\s+-\s+Página\s+n\.º\s+\d+'
    )
t_Header = re.compile(r'^\d{1,2}\s-\s.*$')
t_SubHeader = re.compile(r'^\d{1,2}\.\d{1,2}\s-\s.*$')
t_ListItem01 = re.compile(r'^.+:.+$')
t_ListItem02 = re.compile(r'^(?:[A-Z](?:\d+)?|\d|[a-z]\.\d)\s*-\s+.+$')
t_Paragraph = re.compile(r'^.*$')

lexicon = (
    (None, lambda t: not t),
    (None, lambda t: t_Ignore.match(t)),
    ('Header', lambda t: t_Header.match(t)),
    ('SubHeader', lambda t: t_SubHeader.match(t)),
    ('ListItem', lambda t: t_ListItem02.match(t)),
    ('ListItem', lambda t: t_ListItem01.match(t)),
    ('Paragraph', lambda t: t_Paragraph.match(t)),
    )

# Parser configuration
parser_rules = {
    'Header': '<h1>%s</h1>',
    'SubHeader': '<h2>%s</h2>',
    'ListItem': '<p class="list_item">%s</p>',
    'Paragraph': '<p>%s</p>',
    }

parse_tender = SimpleParser(
    pre_massage_rules,
    tokenizer_rules,
    lexicon,
    parser_rules,
    post_massage_rules)
