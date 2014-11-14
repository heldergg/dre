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

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

# PDFMiner

from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage

# Django general
from django.conf import settings
from django.db.utils import IntegrityError

# Local Imports
from dreapp.models import Document, DocumentNext
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
## Constants
##

NEW = 1
MODIFY = 2

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


##
## Scraper
##

class DREReader( object ):
    def __init__( self, date ):
        self.date = date
        self.base_url = 'https://dre.pt'
        self.url = None
        self.serie = None

    def soupify(self, html):
        self.soup = bs4.BeautifulSoup(html)

    def check_dirs(self):
        date = self.date
        archive_dir = os.path.join( ARCHIVEDIR,
                                    '%d' % date.year,
                                    '%02d' % date.month,
                                    '%02d' % date.day )
        # Create the directory if needed
        if not os.path.exists( archive_dir ):
            os.makedirs( archive_dir )

        return archive_dir

    def save_pdf(self, meta):
        archive_dir = self.check_dirs()
        pdf_file_name = os.path.join( archive_dir, 'dre-%d.pdf' % meta['id'] )
        save_file( pdf_file_name, meta['url'] )
        self.pdf_file_name = pdf_file_name

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
            dl.append(doc)

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

    def save_docs(self, mode = NEW):
        if not self.doc_list:
            logger.critical('Couldn\'t get documents for %s' % self.date.isoformat())
        for doc in self.doc_list:
            if mode == MODIFY:
                try:
                    document = Document.objects.get(claint = doc['id'] )
                    document_next = DocumentNext.objects.get( document = document )
                except ObjectDoesNotExist:
                    mode = NEW
            if mode == NEW:
                document = Document()
                document_next = DocumentNext()

            document.claint       = doc['id']
            document.doc_type     = doc['type']
            document.number       = doc['number']
            document.emiting_body = doc['source']
            document.source       = '%d.ª Série, Nº %s, de %s' % (
                                self.serie, doc['dr_number'], self.date.isoformat())
            document.dre_key      = 'NA'
            document.in_force     = True
            document.conditional  = False
            document.processing   = False
            document.date         = doc['date']
            document.notes        = doc['summary']
            document.plain_text   = ''
            document.dre_pdf      = doc['url']
            document.pdf_error    = False
            document.timestamp    = datetime.datetime.now()
            try:
                document.save()
            except IntegrityError:
                # Duplicated document
                logger.debug('We have this document. Aborting - %(type)s %(number)s claint=%(id)d' % doc )
                continue

            # Log document
            txt = 'Document saved:\n'
            for key,item in doc.items():
                if key != 'next':
                    txt += '   %-10s: %s\n' % (key, item)
            logger.warn(txt[:-1])

            # Create the document html cache
            if document.plain_text:
                DocumentCache.objects.get_cache(document)

            # Save PDF:
            self.save_pdf( doc )
            time.sleep(0.5)
            logger.debug('ID: %d http://dre.tretas.org/dre/%d/' % (document.id, document.id) )

            # Save the 'next' information to DocumentNext
            document_next.document = document
            document_next.doc_type = doc['next']['type'] if doc['next'] else ''
            document_next.number   = doc['next']['number'] if doc['next'] else ''
            document_next.save()

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
    dr =  DREReader1S( datetime.datetime.strptime( '2014-10-08', '%Y-%m-%d' ) )
    dr.read_index()
    dr.save_docs()

##     k = 0
##     for doc in dr.doc_list:
##         if k==2:
##             doc.save_pdf()
##             doc.extract_txt()
##             doc.process_txt()
##             doc.process_lines()
##         k+=1

if __name__ == '__main__':
    main()
