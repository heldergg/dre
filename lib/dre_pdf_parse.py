# -*- coding: utf-8 -*-

'''
Convert the PDF documents to html
'''

##
# Imports
##

import re

import dreapp

##
# Utils
##

# TODO: This should be on its own module

from cStringIO import StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.layout import LTLine, LTRect, LTCurve, LTTextBoxHorizontal
from pdfminer.pdfpage import PDFPage

def convert_pdf_to_txt(path):
    '''
    Converts PDF to text using the pdfminer library
    '''
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    file_handle = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(
            file_handle,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    file_handle.close()
    device.close()
    retstr.close()
    return text

##
# Box operations
##

#         +----------+ (x1,y1)
#         |          |
#         |  box     |
#         |          |
# (x0,y0) +----------+

def box_intercepts(a_box, b_box):
    '''
    Box operations
    Checks if a_box intercepts b_box
    '''
    ax0, ay0, ax1, ay1 = a_box
    bx0, by0, bx1, by1 = b_box
    return ax0 <= bx1 and ax1 >= bx0 and ay0 <= by1 and ay1 >= by0

def box_envelope(a_box, b_box):
    '''
    Box operations
    Returns a box containing both a_box and b_box
    '''
    ax0, ay0, ax1, ay1 = a_box
    bx0, by0, bx1, by1 = b_box
    return min(ax0, bx0), min(ay0, by0), max(ax1, bx1), max(ay1, by1)

def box_spans_columns(page_box, box):
    '''
    Box operations
    Checks if box spans two columns in the page
    '''
    px0, py0, px1, py1 = page_box
    x0, y0, x1, y1 = box
    half_width = (px1 - px0)/2
    return x0 < half_width and x1 > half_width

def box_outside( page_box, box):
    '''
    Box operations
    Checks if a box has corners outside page_box
    '''
    px0, py0, px1, py1 = page_box
    x0, y0, x1, y1 = box
    return x0 < px0 or x1 > px1 or y0 < py0 or y1 > py1

def convert_pdf_to_txt_layout(path, allowed_areas):
    '''
    Converts PDF to text using the pdfminer library
    '''
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    #device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    file_handle = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()
    non_printable_re = re.compile(ur'(?:%s)' % '|'.join(
        [ chr(i) for i in range(1,31) if i != 10 ]))
    txt = []

    print "#" * 80

    for page in PDFPage.get_pages(
            file_handle,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=True):
        interpreter.process_page(page)
        layout = device.get_result()
        ignore = []

        # Identify areas to ignore
        for obj in layout:
            if ( obj.x0 < 0 or obj.y0 < 0 or
                 obj.x1 > page.mediabox[2] or
                 obj.y1 > page.mediabox[3]):
                continue
            if type(obj) == LTRect or type(obj) == LTCurve:
                expanded_region = False
                for i,region in enumerate(ignore):
                    if box_intercepts(obj.bbox, region):
                        ignore[i] = box_envelope(obj.bbox, region)
                        expanded_region = True
                if not expanded_region:
                    ignore.append(obj.bbox)

        # Gather text from non ignored regions
        for obj in layout:
            # Print only Horizontal Text Boxes
            if type(obj) != LTTextBoxHorizontal:
                continue

            # Checks if object is within allowed areas
            if allowed_areas:
                ignore_obj = reduce( lambda x,y: x and y,
                        [box_outside(area, obj.bbox) for area in allowed_areas])
                if ignore_obj:
                    continue

            # Checks if object is within ignored areas
            if ignore:
                ignore_obj = reduce( lambda x,y: x or y,
                        [box_intercepts(obj.bbox, region) for region in ignore])
                if ignore_obj:
                    continue

            obj_txt = obj.get_text()
            obj_txt = non_printable_re.sub( '', obj_txt)
            obj_txt = obj_txt.strip()

            txt.append(u' '.join(obj_txt.split('\n')))

    text = u'\n'.join(txt)

    file_handle.close()
    device.close()
    retstr.close()
    return text
##
#  Lexer and parser
##

class SimpleParser(object):
    '''
    This is a simple yet complete parser. The arguments are:
        pre_massage_rules - list of tuples with replaces to be made on the
            text, before tokenization;
        tokenizer_rules - rules to tokenize the text. This is a dictionary
            containing two sets of rules:
            split_rules - its a regular expression to be used with re.split
            merge_rules - tuple with two functions, the first function if
                applied to the left token, the second one to the right
                token, if both return true the two tokens are merged
        lexicon - a lexicon to characterize the tokens
        parser_rules - dict with the output to be created for each
            definition on the lexicon
        post_massage_rules - replaces to be applied to the final output
    '''
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
    def set_type(self, token):
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
            html.append(self.parser_rules[t_type] % text)
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

##
# Generic legislation parser
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

##
# Pdf parser
##

class ParsePdf(object):
    def __init__(self, doc):
        self.filename = doc.dre_pdf_filename()
        self.doc = doc

    def get_html(self):
        raise NotImplementedError('This is an abstract method.')

    def run(self):
        return self.get_html()

class ParseTenderPdf(ParsePdf):
    def get_html(self):
        txt = convert_pdf_to_txt(self.filename).decode('utf-8')
        txt = txt[txt.find(self.doc.doc_type):]
        return parse_tender.run(txt)

class ParseGenericPdf(ParsePdf):
    def next_doc(self):
        '''
        Get the next document after the current one. This is necessary to
        properly cut the pdf.
        Note, this means that we can only get the text representation after
        getting the complete journal.
        '''
        cur_timestamp = self.doc.timestamp
        cur_dr_number = self.doc.dr_number
        cur_series = self.doc.series
        Document = dreapp.models.Document
        next_document = Document.objects.filter(dr_number__exact=cur_dr_number
                ).filter(series__exact=cur_series
                ).filter(timestamp__gt=cur_timestamp
                ).order_by('timestamp')
        return next_document[0] if next_document else None

    def cut_out_doc(self, txt):
        next_doc=self.next_doc()
        if next_doc:
            next_doc=u'%s n.\xba %s' % (next_doc.doc_type, next_doc.number)
        cur_doc=u'%s n.\xba %s' % (self.doc.doc_type, self.doc.number)
        if next_doc:
            return txt[txt.find(cur_doc):txt.find(next_doc)]
        else:
            return txt[txt.find(cur_doc):]

    def get_html(self):
        allowed_areas = (
                ( 45, 60, 295, 780),
                (297, 60, 550, 780),
                )
        txt = convert_pdf_to_txt_layout(self.filename, allowed_areas)
        txt = self.cut_out_doc(txt)
        return parse_generic_document.run(txt)

def parse_pdf(doc):
    # Public tenders:
    if (doc.doc_type.lower() == u'Anúncio de Procedimento'.lower() or
            doc.doc_type.lower() == u'Aviso de prorrogação de prazo'.lower() or
            doc.doc_type.lower() == u'Declaração de retificação de anúncio'.lower() or
            doc.doc_type.lower() == u'Anúncio de concurso urgente'.lower()):
        return ParseTenderPdf(doc).run()

    # Generic documents:
    return ParseGenericPdf(doc).run()
