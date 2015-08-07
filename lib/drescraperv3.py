# -*- coding: utf-8 -*-

'''This module will scan and scrap the dre.pt site

This is a refactoring to make maintenance easier.
It supersedes the drescraperv2 module.

Usage:

    # Create the reader for a given date 'date':
    day = DREReadDay(date)

    # Cycle through the docs present in 'date'.
    # These can be filtered using two sets of filters:

    # filter_dr - to filter out the series, in the form:
    # { 'no_series_[123]': <boolean value>, }

    # filter_doc - to filter document characteristics, any metadata field can
    # be used, for instance:
    # { 'doc_type': 'decreto', 'number':'58' }
    # If filter_doc is empty no filtering is made, if not a document must
    # match all the filters to be processed

    for doc in day.read_index(filter_dr, filter_doc):
        # Create the document object
        # The default options are:
        # default_options = {
        #        'update': False, # Do not update existing objects
        #        'update_metadata': True,
        #        'update_digesto': True, # Force digesto update even if we have it
        #        'update_cache': True,
        #        'update_inforce': True,
        #        'save_pdf': True,
        #        }
        update_obj = DREDocSave(doc, options)
        try:
            update_obj.save_doc()
        except DREDuplicateError:
            # These errors are ignored since we do not create duplicateds
            pass

'''

##
## Imports
##

# Global imports
import re
import sys
import os
import os.path
import datetime
import urllib2

# Django environment
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'
import django
django.setup()

# Django imports
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Q
from django.db import transaction

# App imports
from dreapp.models import Document, DocumentText

# Local imports
import bs4
from mix_utils import fetch_url
from drelog import logger
import dreapp.index # Necessary to create the indexing events

##
## Constants
##

# URL where to find the list of published journals for a given date
INDEX_URL = ('https://dre.pt/web/guest/pesquisa-avancada/'
             '-/asearch/advanced/maximized?types=DR&dataPublicacao=%s'
            )

JOURNAL_URL = ('https://dre.pt/web/guest/pesquisa-avancada/'
               '-/asearch/%d/details/%d/maximized%s'
              )

DREPT_URL = 'https://dre.pt%s'

DIGESTO_URL = ('https://dre.pt/home/-/dre/%d/details/maximized'
               '?serie=II&parte_filter=32'
              )

DIGESTO_STATUS_URL= ('https://dre.pt/web/guest/analisejuridica/'
                     '-/aj/publicDetails/maximized?diplomaId=%d'
                    )

SYNONYMS = [
    [u'acórdão',
     u'acórdão do supremo tribunal administrativo',
     u'acórdão do supremo tribunal de justiça',
     u'acórdão do tribunal constitucional',
     u'acórdão do tribunal de contas', ],
    [u'acordo colectivo de trabalho', 'acordo coletivo de trabalho' ],
    [u'alvará-extracto', 'alvará (extrato)' ],
    [u'anúncio-extracto', 'anúncio (extrato)' ],
    [u'aviso-extracto', 'aviso (extrato)' ],
    [u'contrato-extracto', 'contrato (extrato)' ],
    [u'declaração de rectificação', 'declaração de retificação' ],
    [u'declaração-extracto', 'declaração (extrato)' ],
    [u'decreto lei', 'decreto-lei' ],
    [u'deliberação-extracto', 'deliberação (extrato)' ],
    [u'despacho-extracto', 'despacho (extrato)' ],
    [u'directiva', 'diretiva' ],
    [u'listagem-extracto', 'listagem (extrato)' ],
    [u'portaria-extracto', 'portaria (extrato)' ],
    [u'regulamento-extracto', 'regulamento (extrato)' ],
    [u'relatório (extrato)', 'relatório-extrato' ],
    [u'decreto lei', 'decreto-lei' ],
    [u'decreto do presidente da república',
     u'decreto',
     u'decreto do representante da república para a região autónoma da madeira' ],
    [u'resolução',
     u'resolução da assembleia da república',
     u'resolução da assembleia legislativa da região autónoma da madeira',
     u'resolução da assembleia legislativa da região autónoma dos açores',
     u'resolução da assembleia nacional',
     u'resolução do conselho de ministros', ],
    ]

ARCHIVEDIR=settings.ARCHIVEDIR

MAX_ATTEMPTS=5

##
## Utilities
##

# Exceptions

class DREParseError(Exception):
    '''
    Could not parse the document
    '''
    pass

class DREDuplicateError(Exception):
    '''
    Duplicated documents
    '''
    pass

class DREFileError(Exception):
    '''
    Error while downloading a file
    '''
    pass

# Functions

def read_soup(page):
    '''
    Reads a web page and soupifies it
    '''
    # Read the page
    html = fetch_url(page)[1]
    # Parse the page
    return bs4.BeautifulSoup(html)

def first_child(soup):
    '''
    Returns the first child of an html element
    '''
    for element in soup.children:
        # Ignore empty elements
        if not str(element.encode('utf-8')).strip():
            continue
        return element
    return None

def strip_html(html):
    '''
    Inserts a line break between <p>aragraphs
    Removes repeated line breaks
    Removes html tags from a string
    '''
    html = html.replace('</p>', '\n').replace('\n\n', '\n')
    # Remove html tags
    txt = re.sub(r'<.*?>', '', html)
    return txt.strip()

def msg_doc(st, doc):
    data = doc.data
    return '%-15s ' % st + '%s %s of %s' % (data['doc_type'], data['number'],
            doc.journal.data['date'].date())

def check_dirs(date):
    archive_dir=os.path.join(ARCHIVEDIR,
                             '%d' % date.year,
                             '%02d' % date.month,
                             '%02d' % date.day)
    # Create the directory if needed
    if not os.path.exists( archive_dir ):
        os.makedirs( archive_dir )
    return archive_dir

def save_file(filename, url):
    k = 1
    data_blob=fetch_url(url)[1]
    with open(filename, 'wb') as f:
        f.write(data_blob)
        f.close()

##
## Read the dre.pt site
##

# Re

# Journal number:
DR_NUMBER_RE = re.compile(r'^(?:Diário da República n.º |'
                          r'Diário do Governo n.º |'
                          r'Diário do Govêrno n.º )'
                          r'(?P<dr_number>[0-9A-Za-z/-]+)'
                          r'.*$')
# Journal dre.pt id
DR_ID_NUMBER_RE = re.compile(r'^https://dre.pt/web/guest/pesquisa-avancada/'
                             r'-/asearch/(?P<int_rd_num>\d+)/details/'
                             r'maximized.*$')

# Document type and number:
DOCTYPE_NUMBER_RE = re.compile(ur'^(?P<doc_type>.*?)(?:\s+n.º\s+)'
                               ur'(?P<number>[0-9A-Za-z\s/-]+)'
                               ur'.*?-\s(?:Diário da República\s+n.º\s+|'
                               ur'Diário do Governo\s+n.º\s+|'
                               ur'Diário do Govêrno\s+n.º\s+)'
                               ur'(?P<dr_number>[0-9A-Za-z/-]+).*$',
                               flags=re.U)

DOCTYPE_NONUMBER_RE = re.compile(ur'^(?P<doc_type>.*?)(?:\s+-\s+)'
                                 ur'(?:Diário da República\s+n.º\s+|'
                                 ur'Diário do Governo\s+n.º\s+|'
                                 ur'Diário do Govêrno\s+n.º\s+)'
                                 ur'(?P<dr_number>[0-9A-Za-z/-]+).*$')

NODOCTYPE_NONUMBER_RE = re.compile(ur'^\(Sem diploma\)'
                                   ur'.*?(?:Diário da República\s+n.º\s+|'
                                   ur'Diário do Governo\s+n.º\s+|'
                                   ur'Diário do Govêrno\s+n.º\s+)'
                                   ur'(?P<dr_number>[0-9A-Za-z/-]+).*$')

# Scraper

class DREReadDoc(object):
    '''
    Document metadata reader
    '''
    def __init__(self, soup, journal):
        self.data = {}
        self.journal = journal
        self.parse(soup)

    ##
    # Parser

    def parse_emiting_body(self, soup):
        self.data['emiting_body'] = soup.find('div', {'class': 'author'}
                                              ).renderContents().strip()

    def parse_notes(self, soup):
        try:
            notes = strip_html(soup.find('div', {'class': 'summary'}
                                        ).renderContents())
        except AttributeError:
            notes = ''
        self.data['notes'] = notes

    def parse_claint(self, tag):
        claint = int(tag['href'].split('/')[-1])
        self.data['claint'] = claint

    def parse_pdfurl(self, tag):
        pdf_url = DREPT_URL % tag['href']
        self.data['pdf_url'] = pdf_url

    def parse_doc_type_number(self, text):
        # If we have document type and number:
        try:
            dtn = DOCTYPE_NUMBER_RE.match(text)
            self.data['doc_type'] = dtn.group('doc_type').strip()
            self.data['number'] = dtn.group('number').strip()
            return
        except AttributeError:
            pass

        # We have a document type but no number
        try:
            dtn = DOCTYPE_NONUMBER_RE.match(text)
            self.data['doc_type'] = dtn.group('doc_type').strip()
            self.data['number'] = ''
            return
        except AttributeError:
            pass

        # No document, no document number
        if 'Sem diploma' in text:
            self.data['doc_type'] = 'Não especificado'
            self.data['number'] = ''
            return

        raise DREParseError('Could not parse the document: %s' % text)

    def parse_digesto(self, tag):
        try:
            digesto = tag.find('span', { 'class':'rgba' })
            digesto = int(digesto.renderContents())
            if digesto == self.data['claint']:
                digesto = None
        except AttributeError:
            digesto = None
        self.data['digesto'] = digesto

    def parse_header(self, soup):
        '''
        Several types of headers are presented on the document listings:

        i) PDF link plus an rgba number:
            a) If the claint (the pdf number) and the rgba number are different
               then we have a digesto entry;
            b) If If the claint (the pdf number) and the rgba number the same
               there's no digesto entry: for example the first document, series
               1 from 2000-6-1 (Decreto do Presidente da República n.º 27/2000);

        ii) No PDF link or claint
            Example: Second series, 1990-06-02
            These docs do not have claint, we make claint=-1 on these cases

        '''
        header = first_child(soup)
        try:
            # Type i) header
            header_text = header.stripped_strings.next()
            self.parse_claint(header)
            self.parse_pdfurl(header)
            self.parse_digesto(header)
            self.parse_doc_type_number(header_text)
        except AttributeError:
            # Type ii) header
            header_text = header.strip()
            self.parse_doc_type_number(header_text)
            self.data['claint'] = -1
            self.data['pdf_url'] = ''
            self.data['digesto'] = None

    def parse(self, soup):
        self.parse_emiting_body(soup)
        self.parse_notes(soup)
        self.parse_header(soup)

    def filter(self, filter_doc = {}):
        for fl in filter_doc:
            if not (filter_doc[fl].lower() in self.data[fl].lower()):
                return False
        return True


class DREReadJournal(object):
    def __init__(self, soup, date):
        self.data={'date': date}
        self.parse(soup)

    def parse(self, soup):
        # Series
        series_st = soup.find('div',{'class':'serie'}
                ).renderContents().lower().strip()
        series=(1 if series_st == 'série i' else
                2 if series_st == 'série ii' else
                3 if series_st == 'série iii' else None)

        # Parse header:
        source = soup.find('a')['title']

        # DR number
        dr_number = source.split(',')[0].split()[-1]

        # DR internal id
        dr_id_number = int(DR_ID_NUMBER_RE.match(soup.find('a')['href']
            ).groups('DR_NUMBER_RE')[0])

        self.data.update({
                          'series': series,
                          'source': source,
                          'dr_number': dr_number,
                          'dr_id_number': dr_id_number,
                        })

    def filter(self, filter_dr={}):
        exclude_series = [filter_dr.get('no_series_1', False),
                          filter_dr.get('no_series_2', False),
                          filter_dr.get('no_series_3', True),
                          ]
        series = self.data['series']
        for i, fl in enumerate(exclude_series):
            if fl and series == i+1:
                return False
        return True

    def get_document_list(self, soup):
        pagination = soup.find('div', { 'class': 'pagination' })
        if pagination:
            pagination.extract()
            pagination = soup.find('div', { 'class': 'pagination' })
            pagination.extract()
        doc_list_page = soup.find('div', { 'class': 'list' })
        if doc_list_page:
            return doc_list_page.find('ul', recursive=False).find_all('li')
        return []

    def read_index(self):
        dr_id_number = self.data['dr_id_number']
        page = 1
        doc_list = []
        sufix = ''
        while True:
            logger.debug('JOURNAL: Read journal page')
            soup = read_soup(JOURNAL_URL % (dr_id_number, page, sufix))
            doc_page = self.get_document_list(soup)
            for doc in doc_page:
                try:
                    yield DREReadDoc(doc,self)
                except DREParseError:
                    pass
            if not doc_page:
                logger.debug('JOURNAL: Empty page')
                if not sufix and self.data['series']==2:
                    page = 0
                    sufix = '?at=c'
                else:
                    break
            page += 1

class DREReadDay(object):
    '''
    Reads the journal entries metadata for a given day
    '''
    def __init__(self, date):
        self.date = date
        self.index_url = INDEX_URL % date.date()

    def read_index(self, filter_dr = {}, filter_doc={}):
        '''
        Create an index of self.date documents.
        '''
        soup = read_soup(self.index_url
                ).find('div', {'class': 'search-result'}).findAll('li')
        dr_list = (DREReadJournal(dr_soup,self.date) for dr_soup in soup)
        return (doc
                  for dr in dr_list
                      if dr.filter(filter_dr)
                          for doc in dr.read_index()
                              if doc.filter(filter_doc))


class Options(dict):
    '''Class to manage options.'''
    def __init__(self, options, default_options):
        dict.__init__(self, options)
        for opt in default_options:
            self[opt] = self.get(opt, default_options[opt])

NEW=1
UPDATE=2

class DREDocSave(object):
    def __init__(self, doc, options):
        self.doc=doc
        self.mode=NEW
        default_options = {
                'update': False,
                'update_metadata': True,
                'update_digesto': True,
                'update_cache': True,
                'update_inforce': True,
                'save_pdf': True,
                }
        self.options=Options(options, default_options)

    ##
    # Save metadata

    def check_claint(self):
        '''
        Checks if the document is duplicated using dre.pt unique identifier
        '''
        new_site_date=datetime.datetime(2014,9,18)
        claint=self.doc.data['claint']
        try:
            doc_obj=Document.objects.get(claint=claint)
            if doc_obj.timestamp<new_site_date:
                # Do not retrieve documents based on claint that have timestamp
                # before 2014-9-18
                doc_obj=None
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            doc_obj=None
        return doc_obj

    def check_olddocs(self):
        '''
        For dates before the site change we should try to verify
        the document duplication by other means (since the 'claint' changed
        on the new site)
        '''
        date=self.doc.journal.data['date']
        doc_type=self.doc.data['doc_type'].lower()
        number=self.doc.data['number']
        series=self.doc.journal.data['series']
        new_site_date=datetime.datetime(2014,9,18)
        # Test the date
        if date>=new_site_date:
            return None
        # Does the current doc_type have synonyms?
        doc_types=[doc_type]
        for sn in SYNONYMS:
            if doc_type in sn:
                doc_types = sn
        # Create a query for the synonyms:
        dt_qs = Q( doc_type__iexact = doc_types[0] )
        for dt in doc_types[1:]:
            dt_qs = dt_qs | Q( doc_type__iexact = dt )
        # Query the database:
        dl=Document.objects.filter(
                date__exact=date).filter(
                dt_qs).filter(
                number__iexact=number).filter(
                series__exact=series)
        if len(dl)>1:
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
            raise DREDuplicateError('Multiple similar documents')
        elif len(dl)==0:
            return None
        else:
            return dl[0]

    def check_duplicate(self):
        '''
        Returns the Document object if the document is duplicated.
        Otherwise a new object is returned
        '''
        check_list = [
                self.check_claint,
                self.check_olddocs,
                ]
        for check in check_list:
            doc_obj = check()
            if doc_obj:
                self.mode=UPDATE
                return doc_obj
        return Document()

    def save_metadata(self, doc_obj):
        '''
        Saves the metadata to doc_obj
        '''
        doc_data = self.doc.data
        journal_data = self.doc.journal.data
        doc_obj.claint       = doc_data['claint']
        doc_obj.doc_type     = doc_data['doc_type']
        doc_obj.number       = doc_data['number']
        doc_obj.emiting_body = doc_data['emiting_body']
        doc_obj.source       = journal_data['source']
        doc_obj.dre_key      = ''
        doc_obj.in_force     = True
        doc_obj.conditional  = False
        doc_obj.processing   = False
        doc_obj.date         = journal_data['date']
        doc_obj.notes        = doc_data['notes']
        doc_obj.plain_text   = ''
        doc_obj.dre_pdf      = doc_data['pdf_url']
        doc_obj.pdf_error    = False
        doc_obj.dr_number    = journal_data['dr_number']
        doc_obj.series       = journal_data['series']
        doc_obj.timestamp    = datetime.datetime.now()
        doc_obj.save()


    ##
    # Update DIGESTO

    def check_digesto(self, doc_obj):
        '''Checks if the document already has the digesto text'''
        document_text=None
        try:
            document_text = DocumentText.objects.get( document = doc_obj )
        except ObjectDoesNotExist:
            pass
        return document_text

    def get_digesto(self):
        '''Donloads the digesto text'''
        # Gets the DIGESTO system integral text
        soup = read_soup(DIGESTO_URL % self.doc.data['digesto'])
        # Parse the text
        # <li class="formatedTextoWithLinks">
        try:
            text = soup.find( 'li', { 'class': 'formatedTextoWithLinks' }
                    ).renderContents()
            text = text.replace('<span>Texto</span>','')
        except AttributeError:
            # No digesto text, abort
            return ''
        return text

    def save_digesto(self, document_text, doc_obj, text):
        '''
        Saves the document text to the db
        '''
        document_text.document = doc_obj
        document_text.text_url = DIGESTO_URL % self.doc.data['digesto']
        document_text.text = text
        document_text.save()

    def process_digesto(self, doc_obj):
        '''
        Gets more information from the digesto system
        Extracts the document html text from the digesto system
        '''
        # Do we have a digesto entry? If not, return
        if not self.doc.data['digesto']:
            logger.debug(msg_doc('No digesto:', self.doc))
            return
        # Check for digesto text
        document_text=self.check_digesto(doc_obj)
        # If it does not exist or we have a forced update read the html
        if not document_text:
            logger.debug(msg_doc('New digesto:', self.doc))
            document_text = DocumentText()
        elif document_text and self.options['update_digesto']:
            logger.debug(msg_doc('Update digesto:', self.doc))
        else:
            logger.debug(msg_doc('Already have digesto:', self.doc))
            return
        # Get the digesto text
        text = self.get_digesto()
        if not text:
            logger.debug(msg_doc('No digesto text:', self.doc))
            return
        # Save the text
        self.save_digesto(document_text, doc_obj, text)

    ##
    # Update Cache

    def update_cache( self, doc_obj ):
        # Create the document html cache
        if doc_obj.plain_text:
            DocumentCache.objects.get_cache(doc_obj)

    ##
    # Update inforce

    def update_inforce(self, doc_obj):
        # Do we have a digesto entry? If not, return
        if not self.doc.data['digesto']:
            return
        soup=read_soup(DIGESTO_STATUS_URL % self.doc.data['digesto'])
        try:
            text = soup.find( 'div', { 'class': 'naoVigenteDetails' }
                    ).span.renderContents().strip()
            if text == 'Revogado' and doc_obj.in_force:
                doc_obj.in_force = False
                doc_obj.save()
        except AttributeError:
            pass

    ##
    # Save PDF

    def save_pdf(self, doc_obj):
        # If we don't have a pdf to fetch we give up saving the pdf
        if not self.doc.data['pdf_url']:
            return
        # Save the PDF
        archive_dir=check_dirs(self.doc.journal.data['date'])
        pdf_file_name=os.path.join(archive_dir,
                'dre-%d.pdf' % doc_obj.id)
        save_file(pdf_file_name, self.doc.data['pdf_url'])

    ##
    # Main Save

    def save_doc(self):
        # Check for document duplication
        doc_obj = self.check_duplicate()
        if self.mode == UPDATE:
            if not self.options['update']:
                logger.debug(msg_doc('IGNORING duplicated document:',
                    self.doc))
                raise DREDuplicateError('Not going to process this doc.')
            else:
                logger.warn(msg_doc('UPDATE mode:', self.doc))
                logger.debug('doc_obj: %s' % doc_obj)
        else:
            logger.warn(msg_doc('NEW mode:', self.doc))
        # Save metadata
        if self.mode==NEW or (self.mode==UPDATE and
                              self.options['update_metadata']):
            logger.debug(msg_doc('Metadata:', self.doc))
            self.save_metadata(doc_obj)
        # Save digesto
        if self.mode==NEW or (self.mode==UPDATE and
                              self.options['update_digesto']):
            self.process_digesto(doc_obj)
        # Update cache
        if self.mode==NEW or (self.mode==UPDATE and
                              self.options['update_cache']):
            logger.debug(msg_doc('Cache:', self.doc))
            self.update_cache(doc_obj)
        # Update inforce
        if self.mode==NEW or (self.mode==UPDATE and
                              self.options['update_inforce']):
            logger.debug(msg_doc('Update inforce:', self.doc))
            self.update_inforce(doc_obj)
        # Save PDF
        if self.mode==NEW or (self.mode==UPDATE and
                              self.options['save_pdf']):
            logger.debug(msg_doc('Get PDF:', self.doc))
            self.save_pdf(doc_obj)
