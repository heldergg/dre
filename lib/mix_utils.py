#!/usr/bin/env python

'''Scraping application for the dre.pt site, a portuguese database of 
legislation.
'''

# Imports

import cookielib
import re
import socket
import time
import urllib2
import unicodedata
import StringIO
import gzip

from drelog import logger
from dreerror import DREError

######################################################################

def debug_unicode( st ):
    if isinstance( st, unicode):
        return unicodedata.normalize('NFKD', st).encode('ascii','ignore')
    else:
        return unicodedata.normalize('NFKD', unicode( st, 'ascii', 'ignore')).encode('ascii')

du = debug_unicode

######################################################################

# Socket timeout in seconds
socket.setdefaulttimeout(60)
MAXREPEAT = 2

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_301(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301( 
                        self, req, fp, code, msg, headers)              

        result.status = code
        logger.debug('Redirect URL (301): %s' %  result.url)
        return result

    def http_error_302(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_302( 
                        self, req, fp, code, msg, headers)              

        result.status = code
        logger.debug('Redirect URL (302): %s' %  result.url)

        ### DRE ugly hack: the dre.pt site instead of issuing an http error code
        ### redirects to an error page. Here we catch the error and raise an
        ### exception.

        if 'Paginas/Erro.aspx' in result.url:
            raise DREError('Error condition on the site')

        return result

def fetch_url( url, data=None, cj=None ):
    repeat = 1
    while repeat:
        try:
            logger.debug('Getting: %s' % url)
            request = urllib2.Request(url, data)
            request.add_header('Accept-Encoding', 'gzip; q=1.0, identity; q=0.5')
            request.add_header('User-agent', 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; chromeframe/11.0.696.57)')
            if not cj:
                cj = cookielib.LWPCookieJar()
            opener = urllib2.build_opener(SmartRedirectHandler(), urllib2.HTTPCookieProcessor(cj) )
            resource = opener.open( request )
            is_gzip = resource.headers.get('Content-Encoding') == 'gzip'

            payload = resource.read()

            url = resource.url

            resource.close()

            if is_gzip:
                try:
                    compressedstream = StringIO.StringIO(payload)
                    gzipper = gzip.GzipFile(fileobj=compressedstream)
                    payload = gzipper.read()
                except IOError:
                    pass

            repeat = False
        except socket.timeout:
            repeat += 1
            if repeat > MAXREPEAT:
                logger.critical('Socket timeout! Aborting')
                raise
            logger.debug('Socket timeout! Sleeping for 5 minutes')
            time.sleep(300)
        except urllib2.URLError, msg:
            repeat += 1
            if repeat > MAXREPEAT:
                logger.critical('HTTP Error! Aborting. Error repeated %d times: %s' % (MAXREPEAT, msg) )
                raise DREError('Error condition on the site')
            if 'Error 400' in str(msg) or 'Error 404' in str(msg):
                logger.critical('HTTP Error 40x - URL: %s' % url)
                raise
            if 'Error 503' in str(msg):
                logger.critical('HTTP Error 503 - cache problem going to try again in 10 seconds.')
                time.sleep(10)
                continue

            logger.warn('HTTP Error! Sleeping for 5 minutes: %s' % msg)
            time.sleep(300)

    return url, payload, cj
