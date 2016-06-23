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

extract_number_re = re.compile(ur'^.*(\d+)\.º((?:-[A-Z])?)$')

class GenericDocParser(SimpleParser):
    def state_setup(self):
        self.state['i'] = 0
        self.state['t'] = []

    def set_tokenizer_state(self, tok_ord, token):
        self.state['i'] = tok_ord
        self.state['t'].append(token)

    def rule_dispatch(self, t_type, template, text, state ):
        if t_type in ('Article', 'Chapter', 'Section', 'SubSection',
                      'Annex', 'Book', 'Title'):
            number_match = extract_number_re.match(text)
            if number_match:
                number = number_match.group(1) + number_match.group(2)
            else:
                number = ''
            template = u'<a name="%s_%s_%d"></a>' % (t_type, number,
                    state['i']) + template
        return template % text

# Text massager configuration

pre_massage_rules = (
    (r'Decreto - Lei', 'Decreto-Lei'),
    (ur'\s+-', u'-'),
    (ur'-\s+', u'-'),
    (ur'—', '-'),
    (ur'\u2014','-'),
    (ur'DL nº', u'Decreto-Lei n.º'),
    (ur'(?iu)\s([a-zãàáêéôóíç]{2,20})-((?:(?!se).)[a-zãàáêéõôóíç]+)([,\.;:]?)\s',
        ur' \1\2\3 '),
    (ur'(?um)I\s+SÉRIE\nISSN 0870-9963',''),
    (ur'Endere\xe7o Internet: http://dre.pt\nCorreio eletr\xf3nico: dre@incm.pt\nTel.: 21 781 0870 Fax: 21 394 5750',''),
    (ur'Tel.: 21 781 0870 Fax: 21 394 5750','')
    )

post_massage_rules = (
    (r' ;', ';'),
    (r' :', ':'),
    (r'-\s*-', '-'),
    (r'DecretoLei','Decreto Lei')
    )

# Tokenizer configuration
t_is_list = re.compile(r'^(?:(?:[A-Z](?:\d+)?|\d+|[a-z0-9]+\.\d+)\s*-|[a-z]+\))\s+.*$')
t_is_header = re.compile(ur'(?ui)^(?:Artigo \d+\.º(?:-[A-Z])?|Capítulo\s+(?:[ivxld]+|único)|Secção\s+(?:[ivxld]+|única)|Subsecção\s+(?:[ivxld]+|única)|Anexo(?:\s+\[ivxld]+|\s+único)?|Livro\s+(?:[ivxld]+|único)|Título\s+(?:[ivxld]+|único))$')

any_str = lambda t,s: t and t[-1] not in u':\u201d'
dash_start = lambda t,s: t and t[0] == '-' and s['i'] > 1
dash_end = lambda t,s: t and t[-1] == '-' and s['i'] > 1
is_semicolon_or_colon = lambda t,s: t in ';:'
asks_for_continuation = lambda t,s: t and t[-1] == ',' and s['i'] > 1
is_continuation = lambda t,s: t and t[0].islower() and not t_is_list.match(t) and s['i'] > 1
is_not_list_or_header = lambda t,s: (
        not t_is_list.match(t) and
        not t_is_header.match(t) and
        t not in u'«»'
        )
phrase_start = lambda t,s: (
        t and                       # Ignore empty lines
        (                           # Normal phrase starts
            t[0].isupper() or           # Upper case start
            t_is_list.match(t)          # List item start
        ) and
        t[-1] not in u'.:;\u201d' and      # Ignore if sentence is terminated properly
        not t.isupper() and         # Ignore uppercase sentences
        # Headers
        not t_is_header.match(t) and        # Sentence is an header
        ( s['t'] and                        # Sentence comes after an header
          not t_is_header.match(s['t'][-1])
        ) and
        s['i'] > 1                            # Start of the document
        )

tokenizer_rules = {
    'split_rules': ur'(?:\n|(;)|(:)|(«)|(»))',
    'merge_rules': [
        (asks_for_continuation, any_str, 'm1'),
        (dash_end, dash_start, 'm2'),
        (any_str, is_semicolon_or_colon, 'm3'),
        (any_str, is_continuation, 'm4'),
        (phrase_start, is_not_list_or_header, 'm5'),
        ],
    }

# Lexer configuration
t_ListItem01 = re.compile(r'^[A-Z](?:\d+)?\s*-\s+.+$') # Alpha list: A - or A1 -
t_ListItem02 = re.compile(r'^\d+\s*-\s+.+$') # Numeric list: 1 -
t_ListItem03 = re.compile(r'^\d+\.\d+\s*-\s+.+$') # Numeric list: 1.1 -
t_ListItem04 = re.compile(r'^\d+\.\d+\.\d+\s*-\s+.+$') # Numeric list: 1.1.1 -
t_ListItem05 = re.compile(r'^[a-z]+\)\s+.+$') # Alpha list: a) or i) ii)
t_ListItem06 = re.compile(r'^[a-z]\.\d\s*-\s+.+$') # Mixed list: a.1 -
t_Article    = re.compile(ur'Artigo \d+\.º(?:-[A-Z])?')
t_Chapter    = re.compile(ur'(?ui)^Capítulo\s+(?:[ivxld]+|único)$')
t_Section    = re.compile(ur'(?ui)^Secção\s+(?:[ivxld]+|única)$')
t_SubSection = re.compile(ur'(?ui)^Subsecção\s+(?:[ivxld]+|única)$')
t_Annex      = re.compile(ur'(?ui)^Anexo(?:\s+\[ivxld]+|\s+único)?$')
t_Book       = re.compile(ur'(?ui)^Livro\s+(?:[ivxld]+|único)$')
t_Title      = re.compile(ur'(?ui)^Título\s+(?:[ivxld]+|único)$')
t_Paragraph  = re.compile(r'^.*$')

lexicon = (
    (None, lambda t: not t),
    ('QuoteStart', lambda t: t and t[0]==u'«'),
    ('QuoteEnd',   lambda t: t and t[0]==u'»'),
    ('ListItem01', lambda t: t_ListItem01.match(t)),
    ('ListItem02', lambda t: t_ListItem02.match(t)),
    ('ListItem03', lambda t: t_ListItem03.match(t)),
    ('ListItem04', lambda t: t_ListItem04.match(t)),
    ('ListItem05', lambda t: t_ListItem05.match(t)),
    ('ListItem06', lambda t: t_ListItem06.match(t)),
    ('Article',    lambda t: t_Article.match(t)),
    ('Chapter',    lambda t: t_Chapter.match(t)),
    ('Section',    lambda t: t_Section.match(t)),
    ('SubSection', lambda t: t_SubSection.match(t)),
    ('Annex',      lambda t: t_Annex.match(t)),
    ('Book',       lambda t: t_Book.match(t)),
    ('Title',      lambda t: t_Title.match(t)),
    ('Paragraph',  lambda t: t_Paragraph.match(t)),
    )

# Parser configuration

parser_rules = {
    'QuoteStart': '<div style="padding-left:2.5em;">%s',
    'QuoteEnd':   '%s</div>',
    'ListItem01': '<p class="list_item">%s</p>',
    'ListItem02': '<p class="list_item">%s</p>',
    'ListItem03': '<p class="list_item">%s</p>',
    'ListItem04': '<p class="list_item">%s</p>',
    'ListItem05': '<p class="list_item">%s</p>',
    'ListItem06': '<p class="list_item">%s</p>',
    'Book':       '<h1>%s</h1>',
    'Annex':      '<h2>%s</h2>',
    'Title':      '<h2>%s</h2>',
    'Chapter':    '<h3>%s</h3>',
    'Section':    '<h4>%s</h4>',
    'SubSection': '<h5>%s</h5>',
    'Article':    '<h6>%s</h6>',
    'Paragraph':  '<p>%s</p>',
    }

parser_transitions = []

parse_generic_document = GenericDocParser(
    pre_massage_rules,
    tokenizer_rules,
    lexicon,
    parser_rules,
    post_massage_rules,
    parser_transitions)
