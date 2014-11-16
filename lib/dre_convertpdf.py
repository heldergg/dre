# -*- coding: utf-8 -*-

'''
PDF to html convertion of the fdouble columned DR file.
'''

##
## Imports
##

import datetime
import sys
import os.path
import re
import StringIO
import time

# Append the current project path
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

# PDFMiner
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

# Django general
from django.conf import settings

# Local Imports
from dreerror import DREError
from drelog import logger

##
## Settings
##

ARCHIVEDIR = settings.ARCHIVEDIR

##
## Re
##

# Diário da República, 1.ª série — N.º 194 — 8  de  outubro  de  2014
page_header_re = re.compile( ur'^Diário da República.*?\d+\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}$', re.MULTILINE )

page_number_re = re.compile( ur'^\d{4,5}(?:-\(\d+\))?$', re.MULTILINE )

enumeration_start_re = re.compile( ur'^(?:\d+(?:\s(?:—|-)|\.)|[a-zA-Z]\)\s|[ivxdl]+\)\s).*$' )

hyphens_re = re.compile( ur'-.*? ' )

# Artigo 9.°
titles_re = re.compile( ur'^(?:Artigo \d+.(?:º|\xb0)(?:\s?-[A-Z])?|ANEXO(?:\s[ivxdlIVXDL]+)?|Anexo(?:\s[ivxdlIVXDL]+)?)$' )

##
## Utils
##

def pdf_to_txt( fp ):
    rsrcmgr = PDFResourceManager(caching=True)
    outfp = StringIO.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, outfp, codec=codec, laparams=laparams,
                                           imagewriter=None)
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    for page in PDFPage.get_pages(fp, pagenos=set(),
                                  maxpages=0, password='',
                                  caching=True, check_extractable=True):
        page.rotate = page.rotate % 360
        interpreter.process_page(page)
    device.close()
    txt = outfp.getvalue()
    outfp.close()

    return txt


##
## Scraper
##

class DREPDFReader( object ):
    def __init__(self, document ):
        self.meta = document
        try:
            dnext = document.documentnext_set.all()[0]
            if dnext.doc_type:
                self.doc_next = u'%s n.º %s' % ( dnext.doc_type, dnext.number )
            else:
                self.doc_next = ''
        except IndexError:
            self.doc_next = ''

    def extract_txt(self):
        # Convert the pdf to txt
        filename = self.meta.dre_pdf_filename()
        try:
            fp = file(filename, 'rb')
            self.txt = unicode( pdf_to_txt( fp ), 'utf-8' )
            fp.close()
        except IOError:
            self.txt = ''


    def process_txt(self):
        '''Document wide processing methods
        '''
        def raw_document( txt ):
            # Extract the intended document
            doc_header =  u'%s n.º %s' % (self.meta.doc_type, self.meta.number)
            doc_start = txt.find( doc_header )
            if self.doc_next:
                doc_end = txt.find( self.doc_next )
            else:
                doc_end = -1
            return txt[doc_start:doc_end]

        def strip_trailing( txt ):
            # Clean up leading and trailing spaces
            txt = '\n'.join([ ln.strip() for ln in txt.split('\n') ])
            return txt

        def remove_headers( txt ):
            # Remove page headers
            txt = page_header_re.sub('', txt)
            txt = page_number_re.sub('', txt)
            return txt

        def remove_dr_footer( txt ):
            # Remove the final DR footer
            return txt[:txt.find(u'\nI  SÉRIE')]

        tool_list = [
                raw_document,
                strip_trailing,
                remove_headers,
                remove_dr_footer,
                ]
        txt = self.txt
        for tool in tool_list:
            txt = tool( txt )

        self.txt = txt


    def process_lines(self):
        def is_start_para( ln ):
            if titles_re.match(ln):
                return True
            if len(ln) >= 1 and ln[0] in u'ABCDEFGHIJKLMNOPQRSTUVWXYZÉ':
                return True
            if enumeration_start_re.match(ln):
                return True
            return False

        def all_caps( ln ):
            for c in ln:
                # Must loop through the unicode object, else we get
                # a byte for byte loop
                if c in u'abcdefghijklmnopqrstuvwxyzçàáãâèéêóòõôíú':
                    return False
            return True

        def join_para( para ):
            txt_para = ' '.join(para)
            txt_para = txt_para.replace('- ', '-')
            txt_para = txt_para.replace(' -', '-')

            # Remove the hyphenation
            for term in hyphens_re.findall(txt_para):
                term = term.strip()
                if len(term) < 2:
                    continue
                if term[1].isupper():
                    continue
                if term not in [ '-se', ]:
                    txt_para = txt_para.replace( term, term[1:])
            return txt_para

        def title_line( ln ):
            if titles_re.match(ln):
                return True
            return False


        pl = []     # Paragraph list
        para = []   # Current paragraph
        last_char = ''
        sub_title = False

        txt = self.txt
        ln_number = 0
        for ln in txt.split('\n'):
            ln_number += 1
            ln = ln.strip()
            is_title = bool(titles_re.match(ln))
            #if ln.startswith('Artigo'):
            #    print ln_number, [ln], bool(titles_re.match(ln))

            if not ln:
                # Ignore empty lines
                continue

            if ln_number <= 3:
                para.append(ln)
                if ln_number == 3:
                    pl.append(u'<strong>%s</strong>' % join_para(para))
                    para = []
                continue

            if all_caps(ln):
                # Ignore lines in upper case
                continue

            if title_line(ln):
                # Detect title lines
                # Paragraph
                if para:
                    # End of a pragraph and start of another
                    pl.append(join_para(para))
                    para = []
                pl.append(u'<strong>%s</strong>' % join_para( [ln] ))
                last_char = ''
                sub_title = True
                continue

            if is_start_para(ln):
                # Start a new paragraph
                if ( last_char in ['.',';',':'] or
                     enumeration_start_re.match(ln) or
                     sub_title ):
                    # Paragraph
                    if para:
                        # End of a pragraph and start of another
                        if sub_title:
                            pl.append(u'<em>%s</em>' % join_para(para))
                        else:
                            pl.append(join_para(para))
                        para = []
                if sub_title:
                    sub_title = False

            para.append(ln)
            last_char = ln[-1]

        if para:
            pl.append(join_para(para))

        self.txt = '\n'.join( [ u'<p>%s</p>' % p for p in pl ] )


    def run(self):
        self.extract_txt()
        self.process_txt()
        self.process_lines()

        return self.txt

    def plain_txt(self):
        self.run()
        return re.sub( r'<.*?>', '', self.txt)

##
## Main
##

def main():
    print 'Nothing to do! Il dolce far niente...'

if __name__ == '__main__':
    main()

