# -*- coding: utf-8 -*-

'''This module will scan and scrap the dre.pt site'''

##
## Imports
##

from datetime import datetime, timedelta

import re

from mix_utils import fetch_url

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
        print self.cookie_timeout

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

    def run(self):
        if self.is_cookie_stale():
            self.renew_cookie()
            self.renew_marker()

        print self.cookie_timeout
        print self.unique_marker
