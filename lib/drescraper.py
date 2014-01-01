# -*- coding: utf-8 -*-

'''This module will scan and scrap the dre.pt site'''

##
## Imports
##

from datetime import datetime, timedelta
import os
import os.path
import random
import re
import sys
import time
import urllib2

# Append the current project path
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

# Django general
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max

from dreapp.models import Document, DocumentCache, FailedDoc
import dreapp.index
from drelog import logger

# Local Imports
from mix_utils import fetch_url, du
from dreerror import DREError
import bs4


##
## CONST
##

NEW = 1
MODIFY = 2

##
## Scrap the entire site
##

TOLERANCE = timedelta(0, 120)

class DRESession( object ):
    '''This class manages the DRE session:
        * Manages cookies;
        * Accounts for cookie expiration;
        * Gets and manage the url unique marker;
    '''
    def __init__(self):
        self.cookies = None
        self.unique_marker = None
        self.cookie_timeout = datetime(1970,01,01)

    def cookie_is_stale(self):
        return datetime.now() > ( self.cookie_timeout + TOLERANCE )

    def renew_cookie(self):
        url, payload, cj  =  fetch_url('http://www.dre.pt/sug/digesto/rgratis.asp?reg=PCMLex')
        self.cookies = cj
        self.cookie_timeout = datetime.fromtimestamp(list(cj)[0].expires)

    def renew_marker(self):
        logger.warn('Renewing cookies and marker.')
        assert self.cookies != None, 'No cookie jar...'

        url, payload, cj  =  fetch_url('http://digestoconvidados.dre.pt/digesto/Main.aspx?Database=LEX', cj=self.cookies )
        self.unique_marker = re.search(r'\(S\((.+)\)\)', url).groups()[0]
        self.cookies = cj

    def download_page(self, url ):
        if self.cookie_is_stale():
            self.renew_cookie()
            self.renew_marker()

        url, html, cj  =  fetch_url(url % {
            'unique_marker': self.unique_marker, })

        return html


class DREReadDocs( object ):
    '''Reads a document and stores it in the database.
    '''
    def __init__(self, dre_session):
        self.dre_session = dre_session
        self.pdf_error = False

    def fetch_document(self, claint):
        base_url = 'http://digestoconvidados.dre.pt/digesto/(S(%(unique_marker)s))/Paginas'
        url =  base_url + '/DiplomaDetalhado.aspx?claint=%(claint)d' % { 'claint': claint }
        url_pdf =  base_url + '/DiplomaTexto.aspx'

        self.html = self.dre_session.download_page( url )

        try:
            self.html_pdf = self.dre_session.download_page( url_pdf )
            self.pdf_error = False
        except DREError, msg:
            # There are lots of instances where an error is thrown in this
            # PDF page. This errors will be flagged and dealt latter.
            self.pdf_error = True
            self.html_pdf = ''
            logger.error('Error while trying to read the PDF page. Document %d.' % claint )

    def soupify(self):
        self.soup = bs4.BeautifulSoup(self.html)
        self.soup_pdf = bs4.BeautifulSoup(self.html_pdf)

    def parse(self):
        page_result = {}

        page_result['claint'] = self.claint

        page_result['doc_type'] = self.soup.find('td',
                { 'headers': 'tipoDescricaoIDHeader' }
                ).renderContents()

        number = self.soup.find('td',
                { 'headers': 'numeroIDHeader' }
                ).renderContents()

        # Clean html tags and set the flags
        number = re.sub(r'(?:<[a-zA-Z]+.*?>)|(?:</[a-zA-Z]+.*?>)', '', number)
        page_result['in_force'] = not ('Diploma não vigente' in number)
        page_result['conditional'] = ('Vigência condicional' in number)
        number = number.replace('Diploma não vigente','')
        number = number.replace('Vigência condicional','')
        number = number.replace('(2ªSérie)','')

        page_result['number'] = number

        try:
            page_result['emiting_body'] = self.soup.find('td',
                { 'headers': 'entidadesEmitentesIDHeader' }
                ).renderContents()
        except AttributeError:
            page_result['emiting_body'] = 'Não Indicado'

        try:
            page_result['source'] = self.soup.find('td',
                    { 'headers': 'fonteIDHeader' }
                    ).renderContents()
        except AttributeError:
            page_result['source'] = ''


        # dre_key
        try:
            page_result['dre_key'] = self.soup.find('td',
                    { 'headers': 'ChaveDreIDHeader' }
                    ).renderContents()
        except AttributeError:
            page_result['dre_key'] = ''


        # date
        page_result['processing'] = False
        try:
            date_str = self.soup.find('td',
                    { 'headers': 'dataAssinaturaIDHeader' }
                    ).renderContents()
            page_result['processing'] = ('em tratamento' in date_str.lower())
        except AttributeError:
            # Tries to get the date from the legend header
            date_str = self.soup.find('legend').renderContents()
            logger.warn('Date extracted from legend: %s' % date_str)

        search = re.search(r'(\d{2}\.\d{2}\.\d{4})', date_str)
        if search:
            date_str = search.groups()[0]
            page_result['date'] = datetime.strptime( date_str, '%d.%m.%Y')
        else:
            raise DREError('Can\' find the date string.')

        # notes
        notes = self.soup.find('fieldset',
                { 'id': 'FieldsetResumo' }
                ).find('div').renderContents().strip()
        notes = re.sub(r'(?:<[a-zA-Z]+.*?>)|(?:</[a-zA-Z]+.*?>)', '', notes)
        page_result['notes'] = notes

        try:
            page_result['plain_text'] = self.soup_pdf.find('span',
                    { 'id': 'textoIntegral_textoIntegralResidente',
                      'class': 'TextoIntegralMargin' }
                    ).find('a')['href']
        except (TypeError, AttributeError):
            page_result['plain_text'] = ''

        try:
            page_result['dre_pdf'] = self.soup_pdf.find('span',
                    { 'id': 'textoIntegral_imagemDoDre',
                      'class': 'TextoIntegralMargin' }
                    ).find('a')['href']
        except (TypeError, AttributeError):
            page_result['dre_pdf'] = ''

        page_result['pdf_error'] = self.pdf_error

        self.page_result = page_result

        txt = '\n'
        txt += ' claint: %s\n' % page_result['claint']
        txt += ' doc_type: %s\n' % du( page_result['doc_type'] )
        txt += ' number: %s\n' % du( page_result['number'] )
        txt += ' emiting_body: %s\n' % du( page_result['emiting_body'] )
        txt += ' source: %s\n' % du( page_result['source'] )
        txt += ' dre_key: %s\n' % du( page_result['dre_key'] )
        txt += ' in_force: %s\n' %  page_result['in_force']
        txt += ' conditional: %s\n' %  page_result['conditional']
        txt += ' processing: %s\n' %  page_result['processing']
        txt += ' date: %s\n' % page_result['date']
        txt += ' notes: %s\n' % du( page_result['notes'] )
        txt += ' plain_text: %s\n' % du( page_result['plain_text'] )
        txt += ' dre_pdf: %s\n' % du( page_result['dre_pdf'] )
        txt += ' pdf_error: %s' % page_result['pdf_error']
        logger.debug(txt)


    def save(self, mode):
        page_result = self.page_result

        if mode == MODIFY:
            try:
                document = Document.objects.get(claint = page_result['claint'] )
            except ObjectDoesNotExist:
                mode = NEW
        if mode == NEW:
            document = Document()

        document.claint = page_result['claint']
        document.doc_type = page_result['doc_type']
        document.number = page_result['number']
        document.emiting_body = page_result['emiting_body']
        document.source = page_result['source']
        document.dre_key = page_result['dre_key']
        document.in_force = page_result['in_force']
        document.conditional = page_result['conditional']
        document.processing = page_result['processing']
        document.date = page_result['date']
        document.notes = page_result['notes']
        document.plain_text = page_result['plain_text']
        document.dre_pdf = page_result['dre_pdf']
        document.pdf_error = page_result['pdf_error']
        document.timestamp = datetime.now()

        document.save()

        # Create the document html cache
        if document.plain_text:
            DocumentCache.objects.get_cache(document)

        logger.debug('ID: %d http://dre.tretas.org/dre/%d/' % (document.id, document.id) )


    def check_dirs(self):
        date = self.page_result['date']
        archive_dir = os.path.join( settings.ARCHIVEDIR,
                                    '%d' % date.year,
                                    '%02d' % date.month,
                                    '%02d' % date.day )
        # Create the directory if needed
        if not os.path.exists( archive_dir ):
            os.makedirs( archive_dir )

        return archive_dir

    def save_file(self, url, filename):
        try:
            url, data_blob, cookies = fetch_url( url )
        except urllib2.HTTPError:
            self.page_result['pdf_error'] = True
            logger.error('Could not read PDF: %s DOC: %s' % (
                url,
                self.page_result['claint']))
            return

        with open(filename, 'wb') as f:
            f.write(data_blob)
            f.close()

    def save_pdfs( self ):
        page_result = self.page_result

        if not( page_result['plain_text'] or page_result['dre_pdf']):
            return

        archive_dir = self.check_dirs()

        if page_result['plain_text']:
            self.save_file(page_result['plain_text'], os.path.join(archive_dir,
                           'plain-%d.pdf' % page_result['claint']))
        if page_result['dre_pdf']:
            self.save_file(page_result['dre_pdf'], os.path.join(archive_dir,
                           'dre-%d.pdf' % page_result['claint']))


    def read_document( self, claint, mode=MODIFY ):
        logger.debug('*** Getting %d' % claint)
        self.claint = claint

        self.fetch_document(claint)
        self.soupify()
        self.parse()

        self.save_pdfs()
        self.save(mode)

        logger.debug('Document saved.')

MAX_ERROR_CONDITION = 5 # Max number of retries on a given document
MAX_ERROR_DOCUMENT = 5 # Max number of consecutive documents with error

def wait(log_sleep = True):
    stop_periods = settings.STOPTIME
    while True:
        right_now = datetime.now().time()
        wait = False
        for start,end in stop_periods:
            if right_now >= start and right_now <= end:
                wait = True
                break
        if wait:
            if log_sleep:
                logger.debug('Sleeping for a while, until %s.' % end)
                log_sleep = False
            time.sleep(60)
        else:
            break

def check_gaps():
    docs = Document.objects.all().order_by('claint')

    max_claint = docs.aggregate(Max('claint'))['claint__max']
    print max_claint

    k = 1
    for doc in docs:
        while k < doc.claint:
            yield k
            k += 1
        k += 1

check_gaps.abort_on_error = False

def processing_docs():
    docs = Document.objects.filter(processing__exact = True
            ).filter(date__lte = datetime.now() - timedelta(10)
            ).order_by('date')

    for doc in docs:
        yield doc.claint

processing_docs.abort_on_error = False

def last_claint():
    max_claint = Document.objects.aggregate(Max('claint'))['claint__max']
    i = max_claint if max_claint else 0
    while True:
        i += 1
        yield i

last_claint.abort_on_error = True

class DREScrap( object ):
    '''Re-reads and updates a list of documents'''
    def __init__(self, doc_list, mode=MODIFY ):
        self.doc_list = doc_list
        self.reader = DREReadDocs( DRESession() )
        self.mode = mode

    def log_failed_read(self, claint):
        try:
           fdoc = FailedDoc.objects.get(claint=claint)
           fdoc.tries += 1
        except ObjectDoesNotExist:
            fdoc = FailedDoc()
            fdoc.claint = claint
        fdoc.save()
        logger.error('Failure to read document %d. Making a log entry.' % claint)

    def update(self, doc):
        self.reader.read_document(doc, mode=self.mode)

    def run(self):
        error_condition = 0
        error_document = 0
        for doc in self.doc_list():
            # Checks the STOPTIME list
            wait()

            # Get the document:
            while True:
                try:
                    # Update the document
                    self.update(doc)

                    error_condition = 0
                    error_document = 0
                    break

                except DREError, msg:
                    # Error reading the document. Will sleep 20 seconds and then
                    # we try again.
                    error_condition += 1
                    if error_condition <= MAX_ERROR_CONDITION:
                        t = 20.0 * random.random() + 5
                        logger.warn('DRE error condition #%d on the site claint %d. Sleeping %ds.' % (
                            error_condition, doc, t) )
                        time.sleep( t )
                        continue
                    else:
                        error_condition = 0
                        error_document += 1
                        if self.doc_list.abort_on_error and error_document > MAX_ERROR_DOCUMENT:
                            logger.critical('#%d failed atempts to get documents. Giving up.' % MAX_ERROR_DOCUMENT)
                            raise
                        logger.error('Error in document %d. Going to try the next doc. This is the #%d skipped doc.' % ( doc,error_document ))
                        self.log_failed_read( doc )
                        break

                except Exception, msg:
                    raise

            # Wait a bit before trying the next doc
            t = 20.0 * random.random() + 5
            logger.debug('Geting ready to get the next doc. Sleeping %ds' % t)
            time.sleep( t )
