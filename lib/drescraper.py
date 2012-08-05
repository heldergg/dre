# -*- coding: utf-8 -*-

'''This module will scan and scrap the dre.pt site'''

##
## Imports
##

from datetime import datetime, timedelta
import re
import sys
import os.path

# Append the current project path
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

# Django general
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max

from dreapp.models import Document 

# Local Imports
from mix_utils import fetch_url
import bs4 



##
## Scrap the entire site
##

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

    def fetch_document(self, claint):    
        base_url = 'http://digestoconvidados.dre.pt/digesto/(S(%(unique_marker)s))/Paginas'
        url =  base_url + '/DiplomaDetalhado.aspx?claint=%(claint)d' % { 'claint': claint } 
        url_pdf =  base_url + '/DiplomaTexto.aspx' 

        self.html = self.dre_session.download_page( url )
        self.html_pdf = self.dre_session.download_page( url_pdf )

    def soupify(self):
        self.soup = bs4.BeautifulSoup(self.html) 
        self.soup_pdf = bs4.BeautifulSoup(self.html_pdf) 
        
    def parse(self):
        page_result = {}

        page_result['claint'] = self.claint

        page_result['doc_type'] = self.soup.find('td', 
                { 'headers': 'tipoDescricaoIDHeader' }
                ).renderContents() 

        page_result['number'] = self.soup.find('td', 
                { 'headers': 'numeroIDHeader' }
                ).renderContents() 

        page_result['emiting_body'] = self.soup.find('td', 
                { 'headers': 'entidadesEmitentesIDHeader' }
                ).renderContents() 

        page_result['source'] = self.soup.find('td', 
                { 'headers': 'fonteIDHeader' }
                ).renderContents() 
        
        page_result['dre_key'] = self.soup.find('td', 
                { 'headers': 'ChaveDreIDHeader' }
                ).renderContents() 

        page_result['date'] = datetime.strptime(self.soup.find('td', 
                { 'headers': 'dataAssinaturaIDHeader' }
                ).renderContents(), '%d.%m.%Y') 

        page_result['notes'] = self.soup.find('fieldset', 
                { 'id': 'FieldsetResumo' }
                ).find('div').renderContents()

        page_result['plain_text'] = self.soup_pdf.find('span', 
                { 'id': 'textoIntegral_textoIntegralResidente',
                  'class': 'TextoIntegralMargin' }
                ).find('a')['href']  
                

        page_result['dre_pdf'] = self.soup_pdf.find('span', 
                { 'id': 'textoIntegral_imagemDoDre',
                  'class': 'TextoIntegralMargin' }
                ).find('a')['href']  

        import pprint
        pprint.pprint(page_result)


    def save(self):
        pass

    def read_document( self, claint ):
        self.claint = claint 

        self.fetch_document(claint)
        self.soupify()
        self.parse()

        print html

class DREScrap( object ):
    '''Read the documents from the site. Stores the last publiched document.
    '''

    def __init__(self):
        self.reader = DREReadDocs( DRESession() )

    def last_read_doc(self):
        '''Gets the claint of the last read document'''
        max_claint = Document.objects.aggregate(Max('claint'))['claint__max']
        return max_claint if max_claint else 0
    
    def run(self):
        last_claint = self.last_read_doc() + 1
        last_claint = 293064 
        while True:
            print last_claint
            try:
                self.reader.read_document( last_claint )
            except Exception, msg:
                raise 
                break
            finally:
                last_claint += 1

TOLERANCE = timedelta(0, 120)

class DREScraper( object ):
    '''Scraps the entire site'''



    def run(self):
        if self.is_cookie_stale():
            self.renew_cookie()
            self.renew_marker()

        self.claint = 293064

        self.download_page()
        self.soupify()
        self.parse()
        

        print self.cookie_timeout
        print self.unique_marker
