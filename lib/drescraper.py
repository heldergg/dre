# -*- coding: utf-8 -*-

'''This module will scan and scrap the dre.pt site'''

##
## Imports
##

from datetime import datetime, timedelta

import re

from mix_utils import fetch_url
import bs4 

class LawScraper( object ):
    '''Scraps a single document'''
    def __init__(self):
        pass

    def run(self):
        pass


##
## Scrap the entire site
##

TOLERANCE = timedelta(0, 120)

class DREScraper( object ):
    '''Scraps the entire site'''
    def __init__(self):
        self.cookies = None
        self.unique_marker = None
        self.cookie_timeout = datetime(1970,01,01)

    def is_cookie_stale(self):
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

    def download_page(self ):
        url, self.html, cj  =  fetch_url('http://digestoconvidados.dre.pt/digesto/(S(%s))/Paginas/DiplomaDetalhado.aspx?claint=%d' % (self.unique_marker, self.claint))

    def soupify(self):
        self.soup = bs4.BeautifulSoup(self.html) 

    def parse(self):
        page_result = {}
        page_result['claint'] = self.claint
        page_result['doc_type'] = self.soup.find('td', { 'headers': 'tipoDescricaoIDHeader' }
                ).renderContents() 

        page_result['number'] = self.soup.find('td', { 'headers': 'numeroIDHeader' }).renderContents() 

        page_result['emiting_body'] = self.soup.find('td', { 'headers': 'entidadesEmitentesIDHeader' }).renderContents() 

        page_result['source'] = self.soup.find('td', { 'headers': 'fonteIDHeader' }).renderContents() 
        
        page_result['dre_key'] = self.soup.find('td', { 'headers': 'ChaveDreIDHeader' }).renderContents() 
        page_result['date'] = datetime.strptime(self.soup.find('td', { 'headers': 'dataAssinaturaIDHeader' }).renderContents(), '%d.%m.%Y') 

        page_result['notes'] = self.soup.find('fieldset', { 'id': 'FieldsetResumo' }).find('div').renderContents()

        page_result['summary'] = '' # TODO: Delete this field. 
        page_result['plain_text'] = '' 
        page_result['dre_pdf'] = '' 

        import pprint
        pprint.pprint(page_result)

    def run(self):
        if self.is_cookie_stale():
            self.renew_cookie()
            self.renew_marker()

        self.claint = 293063    

        self.download_page()
        self.soupify()
        self.parse()
        

        print self.cookie_timeout
        print self.unique_marker
