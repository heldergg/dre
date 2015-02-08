# -*- coding: utf-8 -*-

'''This module will scan and scrap the dre.pt site

This was codded after the ne DRE site came online around September 2014,
it supersedes the drescraper module.
'''

##
## Imports
##

import datetime
import os.path
import re
import sys
import time
import urllib2

# Append the current project path
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

# Django general
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.utils import IntegrityError

# Local Imports
from dreapp.models import Document, DocumentNext, DocumentText
import dreapp.index
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

digesto_url = 'https://dre.pt/home/-/dre/%d/details/maximized?serie=II&parte_filter=32'

##
## Re
##

doc_nonumber = r'(?P<doc_type>.*?)\s+-\s+'

nonumber_header_re = re.compile( r'^(?P<doc_type>.*?)(?:\s+-\s+)'
                            r'(?:Diário da República n.º |Diário do Governo n.º )'
                            r'(?P<dr_number>[0-9A-Za-z/-]+).*$' )

doc_header_re = re.compile( r'^(?P<doc_type>.*?)(?: n.º )(?P<number>[0-9A-Za-z/-]+)'
                            r'.*?(?:Diário da República n.º |Diário do Governo n.º )'
                            r'(?P<dr_number>[0-9A-Za-z/-]+).*$' )

nodoctype_header_re = re.compile( r'^\(Sem diploma\)'
                            r'.*?(?:Diário da República n.º )'
                            r'(?P<dr_number>[0-9A-Za-z/-]+).*$' )

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

class DREReaderError(Exception):
    pass

class DREReader( object ):
    def __init__( self, date ):
        self.date = date
        self.base_url = 'https://dre.pt'
        self.url = None
        self.series = None
        self.digesto = False

    ##
    ## Getting the data
    ##

    def soupify(self, html):
        return bs4.BeautifulSoup(html)

    def read_page(self, page):
        # Read the page
        url, html, cookie_jar = fetch_url( page )
        # Parse the page
        return self.soupify( html )

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
        day_dr = self.soup.findAll('div', { 'class': self.result_div })

        raw_dl = []
        for dr in day_dr:
            raw_dl += dr.findAll('li')

        dl = []
        prev_doc = {}
        for raw_doc in raw_dl:
            # Header with a link (to a PDF)
            raw_header = raw_doc.a.renderContents().strip()
            has_pdf = True

            if 'DIGESTO' in raw_header:
                # Header is not a link
                raw_header = raw_doc.span.renderContents().strip()
                has_pdf = False

            if 'Sem diploma' in raw_header:
                header = nodoctype_header_re.match( raw_header )
                doc_type = 'Não especificado'
                number = ''
            else:
                try:
                    header = doc_header_re.match( raw_header )
                    doc_type = header.group('doc_type')
                    number = header.group('number')
                except AttributeError:
                    header = nonumber_header_re.match( raw_header )
                    doc_type = header.group('doc_type')
                    number = None

            dr_number = header.group('dr_number')

            try:
                digesto = raw_doc.find('a', { 'class':'clara' }).find( 'span', { 'class': 'rgba' } )
                digesto = int(digesto.renderContents())
            except AttributeError:
                digesto = None

            try:
                summary = strip_html(
                        raw_doc.find('div', {'class': 'summary'}
                            ).renderContents().strip())
            except AttributeError:
                summary = ''

            doc = {
                'url': self.base_url + raw_doc.a['href'],
                'id': int(raw_doc.a['href'].split('/')[-1]),
                'emiting_body': raw_doc.find('div', {'class': 'author'}).renderContents().strip(),
                'summary': summary,
                'doc_type': doc_type,
                'number': number,
                'dr_number': dr_number,
                'date': self.date,
                'digesto': digesto,
                'document': None,
                'next': None
                }

            if prev_doc:
                prev_doc['next'] = doc
            prev_doc = doc
            dl.append(doc)

        self.doc_list = dl

    def read_index(self):
        '''Gets the document list'''
        self.soup = self.read_page( self.url )
        self.get_document_list()
        return self

    def get_digesto( self, doc ):
        document = doc['document']
        doc_id = doc['digesto']

        # Checks if the document already has the digesto text
        try:
            document_text = DocumentText.objects.get( document = document,
                    text_type = 0)
        except ObjectDoesNotExist:
            logger.debug('Getting digesto text.')
        else:
            return

        # Gets the DIGESTO system integral text
        soup = self.read_page( digesto_url % doc_id )

        # Parse the text
        # <li class="formatedTextoWithLinks">
        text = soup.find( 'li', { 'class': 'formatedTextoWithLinks' }
                ).renderContents()
        text = text.replace('<span>Texto</span>','')

        # Save the text to the database
        document_text = DocumentText()
        document_text.document = document
        document_text.text_url = 'digesto_url % doc_id'
        document_text.text = text
        document_text.save()

    ##
    ## Saving the docs
    ##

    def save_doc(self, doc, mode = NEW ):
        if mode == MODIFY:
            try:
                document = Document.objects.get(claint = doc['id'] )
            except ObjectDoesNotExist:
                mode = NEW
        if mode == NEW:
            document = Document()

        document.claint       = doc['id']
        document.doc_type     = doc['doc_type']
        document.number       = doc['number']
        document.emiting_body = doc['emiting_body']
        document.source       = '%d.ª Série, Nº %s, de %s' % (
                            self.series, doc['dr_number'], self.date.strftime('%Y-%m-%d'))
        document.dre_key      = ''
        document.in_force     = True
        document.conditional  = False
        document.processing   = False
        document.date         = doc['date']
        document.notes        = doc['summary']
        document.plain_text   = ''
        document.dre_pdf      = doc['url']
        document.pdf_error    = False
        document.dr_number    = doc['dr_number']
        document.series       = self.series
        document.timestamp    = datetime.datetime.now()

        try:
            sid = transaction.savepoint()
            document.save()
            transaction.savepoint_commit(sid)
        except IntegrityError:
            # Duplicated document
            transaction.savepoint_rollback(sid)
            logger.debug('We have this document: %(doc_type)s %(number)s claint=%(id)d' % doc )
            doc['document'] = Document.objects.get(claint = doc['id'] )
            raise DREReaderError('Duplicate document')

        logger.debug('ID: %d http://dre.tretas.org/dre/%d/' % (document.id, document.id) )

        doc['document'] = document


    def log_doc(self, doc):
        txt = 'Document saved:\n'
        for key,item in doc.items():
            if key not in ('next', 'summary', 'document'):
                txt += '   %-12s: %s\n' % (key, item)
        logger.warn(txt[:-1])

    def create_cache( self, doc ):
        document = doc['document']

        # Create the document html cache
        if document.plain_text:
            DocumentCache.objects.get_cache(document)

    def next_doc(self, doc, mode = NEW ):
        document = doc['document']

        # Save the 'next' information to DocumentNext
        if mode == MODIFY:
            return
        document_next = DocumentNext()
        document_next.document = document
        document_next.doc_type = doc['next']['doc_type'] if doc['next'] else ''
        document_next.number   = doc['next']['number'] if doc['next'] else ''
        document_next.save()

    def save_doc_list(self, mode = NEW):
        if not self.doc_list:
            logger.critical('Couldn\'t get documents for %s' % self.date.isoformat())
        for doc in self.doc_list:
            try:
                self.save_doc( doc, mode )
            except DREReaderError:
                # Duplicated document
                if self.digesto and doc['digesto']:
                    # Check the "digesto" integral text
                    self.get_digesto( doc )
                continue
            if self.digesto and doc['digesto']:
                # Get the "digesto" integral text
                self.get_digesto( doc )
            self.save_pdf( doc )
            self.create_cache( doc )
            self.next_doc( doc )
            self.log_doc( doc )

            time.sleep(1)

class DREReader1S( DREReader ):
    def __init__( self, date ):
        super(DREReader1S, self).__init__(date)
        self.url = 'https://dre.pt/web/guest/home/-/dre/calendar/maximized?day=%s' % date
        self.series = 1
        self.result_div = 'diplomas'

class DREReader2S( DREReader ):
    def __init__( self, date ):
        super(DREReader2S, self).__init__(date)
        year = date.year
        self.url = 'https://dre.pt/web/guest/pesquisa-avancada/-/asearch/advanced/maximized?types=SERIEII&anoDoc=%(year)s&perPage=10000&dataPublicacaoInicio=%(date)s&dataPublicacaoFim=%(date)s' % { 'date': date.date(), 'year': year }
        self.series = 2
        self.result_div = 'search-result'
        self.digesto = True
