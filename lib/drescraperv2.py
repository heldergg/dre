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
import zlib

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
from dreapp.models import Document, DocumentText
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

dr_number_re = re.compile( r'^https://dre.pt/web/guest/pesquisa-avancada/-/asearch/(?P<int_rd_num>\d+)/details/maximized.*$')

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


def read_soup(page):
    '''
    Reads a web page and soupifies it
    '''
    # Read the page
    url, html, cookie_jar = fetch_url( page )
    # Parse the page
    return bs4.BeautifulSoup( html )

##
## Scraper
##

class DREReaderError(Exception):
    pass

class DREReader( object ):
    '''
    Read DRs from dre.pt

    # PDFs

    check_dirs         # Check if a dir to store docs exists, if not, creates it
    save_pdf           # downloads a pdf and saves it to the apropriate dir

    # Metadata

    get_document_list  # Gets the doc list from a search page
    extract_metadata   # Creates metadata from the document_list
    read_index         # downloads the page and creates the meta data

    # Getting the documents

    get_digesto        # Gets the digesto text

    log_doc            # makes a doc entry
    create_cache       # Creates a cache entry

    save_doc           # Saves a document metadata to the database

    save_doc_list      # downloads the doc list obtained on `get_document_list`
    '''

    def __init__( self, date ):
        self.date = date
        self.base_url = 'https://dre.pt'
        self.url = None
        self.url = 'https://dre.pt/web/guest/pesquisa-avancada/-/asearch/advanced/maximized?types=DR&dataPublicacao=%(date)s' % { 'date': date.date() }

    ##
    ## Getting the data
    ##

    # Get the PDFs

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

    # Get the document metadata

    def get_document_list(self, soup):
        pagination = soup.find('div', { 'class': 'pagination' })
        if pagination:
            pagination.extract()
            pagination = soup.find('div', { 'class': 'pagination' })
            pagination.extract()

        day_dr = soup.findAll('div', { 'class': 'list' })

        raw_dl = []
        for dr in day_dr:
            raw_dl += dr.findAll('li')

        return raw_dl


    def extract_metadata(self, raw_dl):
        dl = []
        for raw_doc in raw_dl:
            # Header with a link (to a PDF)
            has_pdf = True
            try:
                raw_header = raw_doc.a.renderContents().strip()
            except AttributeError:
                raw_header = raw_doc.span.renderContents().strip()
                has_pdf = False

            series = 1 if 'Série I ' in raw_header else 2

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
                    number = ''

            dr_number = header.group('dr_number')


            try:
                summary = strip_html(
                        raw_doc.find('div', {'class': 'summary'}
                            ).renderContents().strip())
            except AttributeError:
                summary = ''

            emiting_body = raw_doc.find('div', {'class': 'author'}).renderContents().strip()

            if has_pdf:
                claint = int(raw_doc.a['href'].split('/')[-1])
                url = self.base_url + raw_doc.a['href']
            else:
                sign_str = ( doc_type +
                             number if number else '' +
                             emiting_body
                             )
                claint = zlib.adler32(sign_str)
                url = ''
                digesto = None

            try:
                digesto = raw_doc.find('span', { 'class':'rgba' })
                digesto = int(digesto.renderContents())

                if digesto == claint:
                    digesto = None
            except AttributeError:
                digesto = None

            doc = {
                'url': url,
                'id': claint,
                'emiting_body': emiting_body,
                'summary': summary,
                'doc_type': doc_type,
                'number': number,
                'dr_number': dr_number,
                'date': self.date,
                'digesto': digesto,
                'series': series,
                'document': None,
                }

            dl.append(doc)

        return dl


    def read_index(self):
        '''Gets the document list'''
        doc_list = []

        soup = read_soup( self.url )
        dr_list = soup.find('div', { 'class': 'search-result' }).findAll('li')
        for dr in dr_list:
            a = dr.a
            dr_internal_id = int(dr_number_re.match(a['href']).groups('dr_number_re')[0])
            series = 1 if 'Série I ' in a.renderContents() else 2

            # Falta descobrir como extraír os contratos, se estivermos
            # na série 2 basta acrescentar &at=c ao url

            page = 1
            get_contracts = series == 2
            url_template = 'https://dre.pt/web/guest/pesquisa-avancada/-/asearch/%d/details/%d/maximized'
            url_template_org = url_template
            while True:
                url = url_template % (dr_internal_id, page)
                soup = read_soup( url )
                raw_doc_list = self.get_document_list( soup )
                if not raw_doc_list:
                    if get_contracts:
                        url_template = 'https://dre.pt/web/guest/pesquisa-avancada/-/asearch/%d/details/%d/maximized?at=c'
                        get_contracts = False
                        page = 1
                        continue
                    else:
                        url_template = url_template_org
                        break
                dl = self.extract_metadata( raw_doc_list )
                doc_list += dl
                page += 1

        self.doc_list = doc_list
        return self


    ##
    ## Saving the docs
    ##

    def get_digesto( self, doc ):
        document = doc['document']
        doc_id = doc['digesto']

        # Checks if the document already has the digesto text
        try:
            document_text = DocumentText.objects.get( document = document )
        except ObjectDoesNotExist:
            logger.warn('Getting digesto text.')
        else:
            return

        # Gets the DIGESTO system integral text
        soup = read_soup( digesto_url % doc_id )

        # Parse the text
        # <li class="formatedTextoWithLinks">
        text = soup.find( 'li', { 'class': 'formatedTextoWithLinks' }
                ).renderContents()
        text = text.replace('<span>Texto</span>','')

        # Save the text to the database
        document_text = DocumentText()
        document_text.document = document
        document_text.text_url = digesto_url % doc_id
        document_text.text = text
        document_text.save()


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
                            doc['series'], doc['dr_number'], self.date.strftime('%Y-%m-%d'))
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
        document.series       = doc['series']
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
            if key not in ('summary', 'document'):
                txt += '   %-12s: %s\n' % (key, item)
        logger.warn(txt[:-1])


    def create_cache( self, doc ):
        document = doc['document']

        # Create the document html cache
        if document.plain_text:
            DocumentCache.objects.get_cache(document)

    def save_doc_list(self, mode = NEW):
        if not self.doc_list:
            logger.critical('Couldn\'t get documents for %s' % self.date.isoformat())
        for doc in self.doc_list:
            try:
                self.save_doc( doc, mode )
            except DREReaderError:
                # Duplicated document: even if the document is duplicated we
                # check for the "digesto" text since sometimes this is created
                # long after the original date of the document.
                if doc['digesto']:
                    # Check the "digesto" integral text
                    self.get_digesto( doc )
                continue
            if doc['digesto']:
                # Get the "digesto" integral text
                self.get_digesto( doc )
            if doc['url']:
                # if we have a pdf then we get it
                self.save_pdf( doc )
            self.create_cache( doc )
            self.log_doc( doc )

            time.sleep(1)
