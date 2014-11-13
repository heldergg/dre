# -*- coding: utf-8 -*-

'''This module will scan and scrap the dre.pt site

This was codded after the ne DRE site came online around September 2014,
it superceds the drescraper module.
'''

##
## Imports
##

import datetime
import sys
import os.path
import re
import urllib2
import StringIO
import time

# Append the current project path
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

# PDFMiner

from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

# Django general
from django.conf import settings

# Local Imports
from mix_utils import fetch_url
from dreerror import DREError
from drelog import logger
import bs4

##
## Settings
##

MAX_ATTEMPTS = 5
ARCHIVEDIR = settings.ARCHIVEDIR

##
## Re
##

doc_header_re = re.compile( r'^(?P<type>.*?)(?: n.º )(?P<number>[0-9A-Za-z/-]+) - Diário da República n.º (?P<dr_number>[0-9A-Za-z/-]+).*$' )

page_header_re = re.compile( r'^Diário da República.*?\d+\s+de\s+(?:janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+\d{4}$', re.MULTILINE )

page_number_re = re.compile( r'^\d{4,5}(?:-\(\d+\))?$', re.MULTILINE )

enumeration_start_re = re.compile( r'^(?:\d+\s(?:—|-)|[a-zA-Z]\)\s|[ivxdl]+\)\s).*$' )

hyphens_re = re.compile( r'-.*? ' )

titles_re = re.compile( r'^(?:Artigo \d+.º(?:-[A-Z])?|ANEXO|)$' )

##
## Utils
##

def strip_html( html ):
    soup = bs4.BeautifulSoup( html )
    # Break text by paragraph
    txt = '\n'.join([ p.renderContents() for p in soup.findAll('p') ])
    # Remove html tags
    txt = re.sub(r'<.*?>','', txt)
    return txt

def save_file(filename, url):
    k = 1
    while True:
        try:
            url, data_blob, cookies = fetch_url( url )
            break
        except urllib2.HTTPError:
            logger.error('Could not read PDF: %s DOC: %s' % ( url, filename))
            k += 1
            if k == MAX_ATTEMPTS:
                raise DREError('Couldn\'t get the PDF: %s' % url )
            logger.debug('Sleeping 2 secs...')
            time.sleep(2)

    with open(filename, 'wb') as f:
        f.write(data_blob)
        f.close()

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
    def __init__(self, meta ):
        self.meta = meta

    def check_dirs(self):
        date = self.meta['date']
        archive_dir = os.path.join( ARCHIVEDIR,
                                    '%d' % date.year,
                                    '%02d' % date.month,
                                    '%02d' % date.day )
        # Create the directory if needed
        if not os.path.exists( archive_dir ):
            os.makedirs( archive_dir )

        return archive_dir

    def save_pdf(self):
        archive_dir = self.check_dirs()
        pdf_file_name = os.path.join( archive_dir, 'dre-%d.pdf' % self.meta['id'] )
        save_file( pdf_file_name, self.meta['url'] )
        self.pdf_file_name = pdf_file_name

    def extract_txt(self):
        # Convert the pdf to txt
        fp = file(self.pdf_file_name, 'rb')
        self.txt = pdf_to_txt( fp )
        fp.close()


    def process_txt(self):
        '''Document wide processing methods
        '''
        def raw_document( txt ):
            # Extract the intended document
            doc_start = txt.find( '%s n.º %s' % (self.meta['type'],
                self.meta['number']) )
            if self.meta['next']:
                doc_end = txt.find( '%s n.º %s' % (self.meta['next']['type'],
                    self.meta['next']['number']) )
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
            return txt[:txt.find('\nI  SÉRIE')]

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
            if len(ln) >= 1 and ln[0] in "ABCDEFGHIJKLMNOPQRSTUVWXYZÉ":
                return True
            if enumeration_start_re.match(ln):
                return True
            return False

        def all_caps( ln ):
            for c in unicode(ln,'utf-8'):
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
                if term[1].isupper():
                    continue
                if term not in [ '-se', ]:
                    txt_para = txt_para.replace( term, term[1:])
            return txt_para

        pl = []     # Paragraph list
        para = []   # Current paragraph
        last_char = ''
        sub_title = True

        txt = self.txt
        ln_number = 0
        for ln in txt.split('\n'):
            ln_number += 1
            ln = ln.strip()
            is_title = bool(titles_re.match(ln))

            if not ln:
                # Ignore empty lines
                continue

            if all_caps(ln):
                # Ignore lines in upper case
                continue

#            if len(ln) < 30 and ln[-1] not in ['.',';',':'] and para:
#                # Titles
#                pl.append(join_para( para ))
#                pl.append(ln)
#                para = []
#                title = True
#                continue

            if is_start_para(ln):
                # Start a new paragraph
                if ( last_char in ['.',';',':'] or
                     enumeration_start_re.match(ln) ):
                    # Paragraph
                    if para:
                        # End of a pragraph and start of another
                        pl.append(join_para(para))
                        para = []
                elif ln_number == 1:
                    # First line
                    pl.append(join_para([ln]))
                    last_char = ''
                    para = []
                    continue
                elif is_title or sub_title:
                    if para:
                        pl.append(join_para(para))
                        para = []
                    pl.append(join_para([ln]))
                    last_char = ''
                    sub_title = is_title
                    continue

            para.append(ln)
            last_char = ln[-1]

        if para:
            pl.append(join_para(para))

        self.txt = '\n'.join(pl)

        for p in pl:
            print p
            print


class DREReader( object ):
    def __init__( self, date ):
        self.date = date
        self.base_url = 'https://dre.pt'
        self.url = None
        self.serie = None

    def soupify(self, html):
        self.soup = bs4.BeautifulSoup(html)

    def get_document_list(self):
        day_dr = self.soup.findAll('div', { 'class': 'diplomas' })

        raw_dl = []
        for dr in day_dr:
            raw_dl += dr.findAll('li')

        dl = []
        prev_doc = {}
        for raw_doc in raw_dl:
            header = doc_header_re.match( raw_doc.a.renderContents().strip() )
            doc = {
                'url': self.base_url + raw_doc.a['href'],
                'id': int(raw_doc.a['href'].split('/')[-1]),
                'source': raw_doc.find('div', {'class': 'author'}).renderContents().strip(),
                'summary': strip_html(
                    raw_doc.find('div', {'class': 'summary'}).renderContents().strip()),
                'type': header.group('type'),
                'number': header.group('number'),
                'dr_number': header.group('dr_number'),
                'date': self.date,
                'next': None
                }

            if prev_doc:
                prev_doc['next'] = doc
            prev_doc = doc
            dl.append(DREPDFReader(doc))

        self.doc_list = dl

    def read_index(self):
        # Read the page
        if not(self.url):
            raise DREError( 'DRE url to retrieve not defined.' )
        url, html_index, cookie_jar = fetch_url( self.url )

        # Parse the page
        self.soupify( html_index )
        self.get_document_list()

        return self


class DREReader1S( DREReader ):
    def __init__( self, date ):
        super(DREReader1S, self).__init__(date)
        self.url = 'https://dre.pt/web/guest/home/-/dre/calendar/maximized?day=%s' % date
        self.serie = 1


##
## Main
##

def main():
    # Get the DR from a given day
    # This will read the documents for the first series from a given
    # day, save the meta-data to the database, and the pdf to a file
    dr =  DREReader1S( datetime.datetime.strptime( '2014-10-08', '%Y-%m-%d' )
            ).read_index()

    k = 0
    for doc in dr.doc_list:
        if k==2:
            doc.save_pdf()
            doc.extract_txt()
            doc.process_txt()
            doc.process_lines()
        k+=1

if __name__ == '__main__':
    main()
