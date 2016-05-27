# -*- coding: utf-8 -*-

'''
Convert the PDF documents to html
'''

##
# Imports
##

import re

##
# Utils
##

# TODO: This should be on its own module

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set()

    for page in PDFPage.get_pages(
            fp,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    fp.close()
    device.close()
    retstr.close()
    return text

##
#  Lexer and parser
##

class SimpleParser(object):
    def __init__(self,
            pre_massage_rules,
            tokenizer_rules,
            lexicon,
            parser_rules,
            post_massage_rules):
        self.pre_massage_rules = pre_massage_rules
        self.post_massage_rules = post_massage_rules
        self.split_rules = tokenizer_rules['split_rules']
        self.merge_rules = tokenizer_rules['merge_rules']
        self.lexicon = lexicon
        self.parser_rules = parser_rules

    # Massager
    def massager(self, txt, rules):
        for pattern, replace in rules:
            txt = re.sub(pattern, replace, txt)
        return txt

    # Tokenizer
    def tokens(self, txt):
        return (token.strip()
                    for token in re.split(self.split_rules, txt)
                        if token)

    def tokenizer(self, txt):
        first_token = self.tokens(txt).next()
        for token in self.tokens(txt):
            for first_test, second_text in self.merge_rules:
                if first_test(first_token) and second_text(token):
                    token = u' '.join((first_token, token))
                    first_token = token
                    break
            if first_token != token:
                yield first_token
                first_token = token
        yield token


    # Lexer
    def set_type(self,token):
        if u'Diário da República' in token:
            print [token]
            print t_Ignore.match(token)
        for t_type, test in self.lexicon:
            is_match = test(token)
            if is_match and t_type:
                return (t_type, token)
            elif is_match and not t_type:
                # Skip token
                break

    def lexer(self, tokens):
        for token in tokens:
            token = self.set_type(token)
            if token:
                yield token
    # Parser
    def parser(self, tokens):
        html = []
        for t_type, text in tokens:
            html.append(parser_rules[t_type] % text)
        return u'\n'.join(html)

    # Main
    def run(self, txt):
        txt = self.massager(txt, self.pre_massage_rules)
        tokens = self.tokenizer(txt)
        tokens = self.lexer(tokens)
        parsed = self.parser(tokens)
        parsed = self.massager(parsed, self.post_massage_rules)
        return parsed

##
# Parse "Anúncio de Procedimento"
##

# Text massager configuration

pre_massage_rules = (
        (r'Decreto - Lei', 'Decreto-Lei'),
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
t_Ignore = re.compile(ur'(?ui)^Diário\s+da\s+República,\s+2\.ª\s+série\s+-\s+N\.º\s+\d+\s+-\s+\d+\s+de\s+[a-zç]+\s+de\s+\d{4}\s+-\s+Anúncio\s+de\s+procedimento\s+n\.º\s+\d+/\d{4}\s+-\s+Página\s+n\.º\s+\d+')
t_Header = re.compile(r'^\d{1,2}\s-\s.*$')
t_SubHeader = re.compile(r'^\d{1,2}\.\d{1,2}\s-\s.*$')
t_ListItem01 = re.compile(r'^.+:.+$')
t_ListItem02 = re.compile(r'^(?:[A-Z](?:\d+)?|\d|[a-z]\.\d)\s*-\s+.+$')
t_Paragraph = re.compile(r'^.*$')

lexicon = (
        (None,        lambda t: not t),
        (None,        lambda t: t_Ignore.match(t)),
        ('Header',    lambda t: t_Header.match(t)),
        ('SubHeader', lambda t: t_SubHeader.match(t)),
        ('ListItem',  lambda t: t_ListItem02.match(t)),
        ('ListItem',  lambda t: t_ListItem01.match(t)),
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

##
# Pdf parser
##

class ParsePdf(object):
    def __init__(self, doc):
        self.filename=doc.dre_pdf_filename()
        self.doc=doc

    def get_html(self):
        raise NotImplementedError('This is an abstract method.')

    def run(self):
        return self.get_html()

class ParseTenderPdf(ParsePdf):
    def get_html(self):
        txt = convert_pdf_to_txt(self.filename).decode('utf-8')
        txt = txt[txt.find(u'Anúncio de procedimento'):]
        return parse_tender.run(txt)


def parse_pdf(doc):
    if doc.doc_type.lower() == u'Anúncio de Procedimento'.lower():
        return ParseTenderPdf(doc).run()
    return ''
