#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Scraping application for the dre.pt site, a portuguese database of 
legislation.
'''

# Imports

import sys
import os.path

sys.path.append(os.path.abspath('../lib/'))

import urllib2
import urllib
import cookielib
import socket
import re

from drelog import logger
from bs4 import BeautifulSoup

######################################################################

# Socket timeout in seconds
socket.setdefaulttimeout(60)
MAXREPEAT = 6

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):     
    def http_error_301(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_301( 
                        self, req, fp, code, msg, headers)              

        result.status = code
        logger.debug('Redirect URL: %s' %  result.url)
        return result

    def http_error_302(self, req, fp, code, msg, headers):  
        result = urllib2.HTTPRedirectHandler.http_error_302( 
                        self, req, fp, code, msg, headers)              

        result.status = code
        logger.debug('Redirect URL: %s' %  result.url)
        return result

def fetch_url( url, data=None, cj=None ):
    repeat = 1
    while repeat:
        try:
            logger.debug('Getting: %s' % url)
            request = urllib2.Request(url, data)
            request.add_header('Accept-Encoding', 'gzip; q=1.0, identity; q=0.5')
            request.add_header('User-agent', 'Mozilla/5.0')
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
            logger.critical('Socket timeout! Sleeping for 5 minutes')
            time.sleep(300)
        except urllib2.URLError, msg:
            repeat += 1
            if repeat > MAXREPEAT:
                logger.critical('HTTP Error! Aborting. Error repeated %d times: %s' % (MAXREPEAT, msg) )
                raise
            if 'Error 400' in str(msg) or 'Error 404' in str(msg):
                logger.critical('HTTP Error 40x - URL: %s' % url)
                return '' 
            if 'Error 503' in str(msg):
                logger.critical('HTTP Error 503 - cache problem going to try again in 10 seconds.')
                time.sleep(10)
                continue

            logger.critical('HTTP Error! Sleeping for 5 minutes: %s' % msg)
            time.sleep(300)

    return url, payload, cj


def extract_form_fields(soup):
    "Turn a BeautifulSoup form in to a dict of fields and default values"
    # Copied from: https://gist.github.com/104413
    fields = {}
    for input in soup.findAll('input'):
        # ignore submit/image with no name attribute
        if input['type'] in ('submit', 'image') and not input.has_key('name'):
            continue
        
        # single element nome/value fields
        if input['type'] in ('text', 'hidden', 'password', 'submit', 'image'):
            value = ''
            if input.has_key('value'):
                value = input['value']
            fields[input['name']] = value
            continue
        
        # checkboxes and radios
        if input['type'] in ('checkbox', 'radio'):
            value = ''
            if input.has_key('checked'):
                if input.has_key('value'):
                    value = input['value']
                else:
                    value = 'on'
            if fields.has_key(input['name']) and value:
                fields[input['name']] = value
            
            if not fields.has_key(input['name']):
                fields[input['name']] = value
            
            continue
        
        assert False, 'input type %s not supported' % input['type']
    
    # textareas
    for textarea in soup.findAll('textarea'):
        fields[textarea['name']] = textarea.string or ''
    
    # select fields
    for select in soup.findAll('select'):
        value = ''
        options = select.findAll('option')
        is_multiple = select.has_key('multiple')
        selected_options = [
            option for option in options
            if option.has_key('selected')
        ]
        
        # If no select options, go with the first one
        if not selected_options and options:
            selected_options = [options[0]]
        
        if not is_multiple:
            assert(len(selected_options) < 2)
            if len(selected_options) == 1:
                value = selected_options[0]['value']
        else:
            value = [option['value'] for option in selected_options]
        
        fields[select['name']] = value

    for key in fields:
        value = fields[key]
        fields[key] = unicode(value).encode('latin1')
    
    return fields


print "# Get the cookies"
url, payload, cj  =  fetch_url('http://www.dre.pt/sug/digesto/rgratis.asp?reg=PCMLex')

print "# Get the form"
url, payload, cj  =  fetch_url('http://digestoconvidados.dre.pt/digesto/Main.aspx?Database=LEX', cj=cj)
form = BeautifulSoup(payload).find('form', {'id':'Form1'})

print "# Find the url unique marker"
url_marker = re.search(r'\(S\((.+)\)\)', url).groups()[0]
print url_marker

print "# Download a page"
docid = 293063
url, payload, cj  =  fetch_url('http://digestoconvidados.dre.pt/digesto/(S(%s))/Paginas/DiplomaDetalhado.aspx?claint=%d' % (url_marker, docid))

print "# Download PDF Location"
url, payload, cj = fetch_url('http://digestoconvidados.dre.pt/digesto/(S(%s))/Paginas/DiplomaTexto.aspx' % url_marker)

print payload




sys.exit(0)


fields = extract_form_fields(form)
fields['PesquisaDetalhe:valor3'] = '2012.04.12'
fields = urllib.urlencode( fields )


# IMPORTANT NOTE: If there's only one return value, the form will return 
# the result meta data page.

# import pprint
# pprint.pprint( extract_form_fields(form) )

# NO COOKIE NO DATA!
# Should we use the mechanize lib?

print "# Get the data"
print cj

a,b,cj = fetch_url( url, fields , cj)

