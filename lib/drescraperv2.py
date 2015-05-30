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
from difflib import SequenceMatcher as SM

# Append the current project path
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

# Django general
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.utils import IntegrityError
from django.db.models import Q


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
digesto_status_url = 'https://dre.pt/web/guest/analisejuridica/-/aj/publicDetails/maximized?diplomaId=%d'

synonyms = [
    [ 'acórdão',
      'acórdão do supremo tribunal administrativo',
      'acórdão do supremo tribunal de justiça',
      'acórdão do tribunal constitucional',
      'acórdão do tribunal de contas', ],
    [ 'acordo colectivo de trabalho', 'acordo coletivo de trabalho' ],
    [ 'alvará-extracto', 'alvará (extrato)' ],
    [ 'anúncio-extracto', 'anúncio (extrato)' ],
    [ 'aviso-extracto', 'aviso (extrato)' ],
    [ 'contrato-extracto', 'contrato (extrato)' ],
    [ 'declaração de rectificação', 'declaração de retificação' ],
    [ 'declaração-extracto', 'declaração (extrato)' ],
    [ 'decreto lei', 'decreto-lei' ],
    [ 'deliberação-extracto', 'deliberação (extrato)' ],
    [ 'despacho-extracto', 'despacho (extrato)' ],
    [ 'directiva', 'diretiva' ],
    [ 'listagem-extracto', 'listagem (extrato)' ],
    [ 'portaria-extracto', 'portaria (extrato)' ],
    [ 'regulamento-extracto', 'regulamento (extrato)' ],
    [ 'relatório (extrato)', 'relatório-extrato' ],
    [ 'decreto lei', 'decreto-lei' ],
    [ 'decreto do presidente da república',
      'decreto',
      'decreto do representante da república para a região autónoma da madeira' ],
    [ 'resolução',
      'resolução da assembleia da república',
      'resolução da assembleia legislativa da região autónoma da madeira',
      'resolução da assembleia legislativa da região autónoma dos açores',
      'resolução da assembleia nacional',
      'resolução do conselho de ministros', ],
    ]

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
    html = html.replace('</p>','\n').replace('\n\n','\n')
    # Remove html tags
    txt = re.sub(r'<.*?>','', html)
    return txt.strip()


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

def st_ratio( st1, st2 ):
    st1 = st1.lower().replace( '-', ' ').replace('(','').replace(')','')
    st2 = st2.lower().replace( '-', ' ').replace('(','').replace(')','')
    return SM(None, st1, st2).ratio()

##
## Scraper
##

class DREDuplicateError(Exception):
    pass

class DREScraperError(Exception):
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


    def extract_metadata(self, raw_dl, filter_type, filter_number ):
        dl = []
        for raw_doc in raw_dl:
            # Header with a link (to a PDF)
            has_pdf = True
            try:
                raw_header = raw_doc.a.renderContents().strip()
            except AttributeError:
                try:
                    raw_header = raw_doc.span.renderContents().strip()
                except AttributeError:
                    # Some entries don't have a link or even a <span>
                    # We ignore (for now) these entries.
                    continue
                has_pdf = False

            if 'Série III' in raw_header:
                # Ignore series 3 docs
                continue

            series = 2 if 'série ii' in raw_header.lower() else 1

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
                            ).renderContents())
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
                'date_st': self.date.date(),
                'digesto': digesto,
                'series': series,
                'document': None,
                }

            if filter_type and filter_type not in doc_type.lower():
                continue
            if filter_number and filter_number not in number.lower():
                continue

            dl.append(doc)

        return dl


    def read_index(self, read_series, filter_type, filter_number ):
        '''Gets the document list'''
        doc_list = []

        soup = read_soup( self.url )
        dr_list = soup.find('div', { 'class': 'search-result' }).findAll('li')
        for dr in dr_list:
            a = dr.a
            dr_internal_id = int(dr_number_re.match(a['href']).groups('dr_number_re')[0])
            series = 2 if  'série ii' in a.renderContents().lower() else 1
            if series not in read_series:
                continue

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

                dl = self.extract_metadata( raw_doc_list, filter_type, filter_number )
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
            logger.warn('Getting digesto text: %(doc_type)s %(number)s %(date_st)s' % doc)
        else:
            return

        # Gets the DIGESTO system integral text
        soup = read_soup( digesto_url % doc_id )

        # Parse the text
        # <li class="formatedTextoWithLinks">
        try:
            text = soup.find( 'li', { 'class': 'formatedTextoWithLinks' }
                    ).renderContents()
            text = text.replace('<span>Texto</span>','')
        except AttributeError:
            # No digesto text, abort
            logger.debug('No digesto text.')
            return

        # Save the text to the database
        document_text = DocumentText()
        document_text.document = document
        document_text.text_url = digesto_url % doc_id
        document_text.text = text
        document_text.save()

    def get_in_force_status(self, doc):
        doc_id = doc['digesto']
        document = doc['document']
        soup = read_soup( digesto_status_url % doc_id )

        try:
            text = soup.find( 'div', { 'class': 'naoVigenteDetails' }
                    ).span.renderContents().strip()
            if text == 'Revogado' and document.in_force:
                document.in_force = False
                document.save()
                logger.warning('Update in_force: %(doc_type)s %(number)s %(date_st)s' % doc)
        except AttributeError:
            return

    def update_pdf( self, doc ):
        if doc['url'] and doc['document'].dre_pdf != doc['url']:
            doc['document'].dre_pdf = doc['url']
            doc['document'].save()
            logger.debug('PDF\'s url updated: %(doc_type)s %(number)s %(date_st)s' % doc)

    def check_duplicate( self, doc ):
        # For dates before the site change we should try to verify
        # the document duplication by other means (since the 'claint' changed
        # on the new site
        if doc['date'] < datetime.datetime(2014,9,19):
            # Does the current doc_type have synonyms?
            doc_types = [ doc['doc_type'].lower() ]
            for sn in synonyms:
                if doc['doc_type'].lower() in sn:
                    doc_types = sn

            # Create a query for the synonyms:
            dt_qs = Q( doc_type__iexact = doc_types[0] )
            for dt in doc_types[1:]:
                dt_qs = dt_qs | Q( doc_type__iexact = dt )

            dl = Document.objects.filter(
                    date__exact = doc['date'] ).filter(
                    dt_qs ).filter(
                    number__iexact = doc['number'] ).filter(
                    series__exact = doc['series'] )

            if len(dl) > 1:
                # We have a number of documents that, for a given date, have
                # duplicates with the same number and type. The dates can be
                # listed with:
                # select
                #   count(*), date, doc_type, number
                # from
                #   dreapp_document
                # where
                #   date < '2014-9-18'
                # group by
                #   date, doc_type, number
                # having
                #   count(*) > 1;
                logger.error('Duplicate document in the database: %(doc_type)s %(number)s %(date_st)s' % doc)
                raise DREScraperError('More than one doc with the same number and type.')

            if len(dl) == 1:
                doc['document'] = dl[0]
                raise DREDuplicateError('Duplicate document')

        # For other dates we simply use the db integrity checks to spot a
        # duplicate
        document = doc['document']
        try:
            sid = transaction.savepoint()
            document.save()
            transaction.savepoint_commit(sid)
            logger.debug('ID: %d http://dre.tretas.org/dre/%d/' % (document.id, document.id) )
        except IntegrityError:
            # Duplicated document
            transaction.savepoint_rollback(sid)
            doc['document'] = Document.objects.get(claint = doc['id'] )
            raise DREDuplicateError('Duplicate document')


    def get_db_obj(self, doc):
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

        doc['document'] = document

    def save_doc(self, doc):
        self.get_db_obj( doc )
        self.check_duplicate( doc )

    def log_doc(self, doc):
        txt = 'Document saved:\n'
        for key,item in doc.items():
            if key not in ('summary', 'document'):
                txt += '   %-12s: %s\n' % (key, item)
        logger.debug(txt[:-1])
        logger.warn('Got *new* document: %(doc_type)s %(number)s %(date_st)s' % doc )


    def create_cache( self, doc ):
        document = doc['document']
        # Create the document html cache
        if document.plain_text:
            DocumentCache.objects.get_cache(document)

    def save_doc_list(self):
        if not self.doc_list:
            logger.debug('Couldn\'t get documents for %s' % self.date.isoformat())
        for doc in self.doc_list:
            logger.debug('*** Processing document: %(doc_type)s %(number)s %(date_st)s' % doc )
            try:
                self.save_doc( doc )
            except DREDuplicateError:
                logger.debug('We have this document: %(doc_type)s %(number)s %(date_st)s' % doc )
                # Duplicated document: even if the document is duplicated we
                # check for the "digesto" text since sometimes this is created
                # long after the original date of the document.
                if doc['digesto']:
                    # Check the "digesto" integral text
                    self.get_digesto( doc )
                    # Check if the document is in force
                    self.get_in_force_status( doc )
                # In the new dre.pt the doc's pdf url has changed. Because of
                # this even in duplicated documents we update the pdf url.
                if doc['url']:
                    self.update_pdf( doc )
                continue
            except DREScraperError:
                continue

            # Get the "digesto" integral text
            if doc['digesto']:
                self.get_digesto( doc )
            # Check if the document is in force
            if doc['digesto']:
                self.get_in_force_status( doc )
            # Get the pdf version
            if doc['url']:
                self.save_pdf( doc )
            self.create_cache( doc )
            self.log_doc( doc )

            time.sleep(1)
