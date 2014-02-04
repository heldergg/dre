#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This scripts reads the current blog list from the database and gets the
stats reading from sitemeter.
'''

# Imports

import getopt
import sys
import os.path

sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('../lib/'))
sys.path.append(os.path.abspath('../dre_django/'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

def usage():
    print '''Usage: %(script_name)s [options]\n
    Commands:
        -r
        --read_docs         Reads documents from the site until no more
                            documents are available

        -t
        --read_processing   Re-reads the documents marked as "processing"

        -g
        --read_gaps         Checks the missing claints on sequence

        -u <document_id>
        --read_single <document_id>
                            Reads a single document from the site, this is the
                            table's 'claint' field

        --read_text <document_id>
                            Reads the "integral text" from a document, this is
                            the table's 'id' field

        --check_text        Reads the "integral text" for all suitable docs
                            on the database

        -d
        --dump              Dump the documents to stdout as a JSON list

        -c
        --update_cache      Refresh the document's html cache

        -h
        --help              This help screen

    ''' % { 'script_name': sys.argv[0] }


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'hru:vtdcg',
                                   ['help', 'read_processing', 'read_docs',
                                    'read_gaps', 'read_text=', 'check_text',
                                    'read_single=', 'verbose', 'dump',
                                    'update_cache'])
    except getopt.GetoptError, err:
        print str(err)
        print
        usage()
        sys.exit(1)

    # Defaults
    verbose = False

    for o, a in opts:
        if o in ('-v', '--verbose'):
            verbose = True

    # Commands
    for o, a in opts:
        if o in ('-r', '--read_docs'):
            from drescraper import DREScrap, last_claint
            scraper = DREScrap(last_claint)
            scraper.run()
            sys.exit()

        elif o in ('-t', '--read_processing'):
            from drescraper import DREScrap, processing_docs
            scraper = DREScrap(processing_docs)
            scraper.run()
            sys.exit()

        elif o in ('-g', '--read_gaps'):
            from drescraper import DREScrap, check_gaps
            scraper = DREScrap(check_gaps)
            scraper.run()
            sys.exit()

        elif o in ('-u', '--read_single'):
            from drescraper import DREReadDocs, DRESession
            try:
                reader = DREReadDocs( DRESession() )
                document_id = int(a.strip())
                reader.read_document(document_id)
            except ValueError:
                print 'Please specify the document number (integer).'
                sys.exit(1)
            sys.exit()

        elif o == '--read_text':
            from django.core.exceptions import ObjectDoesNotExist
            from drescraper import TIReadDoc
            from dreapp.models import Document

            try:
                document_id = int(a.strip())
                document    = Document.objects.get(pk=document_id)
                reader = TIReadDoc(document)
                reader.read()
            except ValueError:
                print 'Please specify the document number (integer).'
                sys.exit(1)
            except ObjectDoesNotExist:
                print 'The document does not exist.'
                sys.exit(2)
            sys.exit()

        elif o == '--check_text':
            import time
            import random
            from drescraper import TIReadDoc
            from dreapp.models import Document
            from drelog import logger
            from dreerror import DREError

            query = '''
                select
                    id
                from
                    dreapp_document
                where
                    id not in (select document_id from dreapp_documenttext) AND
                    (dre_key like '%%@s1' OR dre_key like '%%@s2');
            '''

            for document in Document.objects.raw(query):
                try:
                    reader = TIReadDoc(document)
                    reader.read()
                except DREError, msg:
                    logger.critical('ID: %d - error getting the document: %s' % (document.id, msg) )
                t = 10.0 * random.random() + 5
                print "Sleeping %ds" % t
                time.sleep(t)

            sys.exit()

        elif o in ('-d', '--dump'):
            import json
            from dreapp.models import Document

            outfile = sys.stdout
            page_size = 5000

            results = Document.objects.all()

            outfile.write('[\n')
            for i in range(0,results.count(), page_size):
                j = i + page_size
                for doc in results[i:j]:
                    json.dump(doc.dict_repr(), outfile, indent=4)
                    outfile.write(',\n')
            outfile.write(']')

            sys.exit()


        elif o in ('-c', '--update_cache'):
            from dreapp.models import Document, DocumentCache
            page_size = 5000

            results = Document.objects.exclude( plain_text__exact = '' )

            for i in range(0,results.count(), page_size):
                j = i + page_size
                print '* Processing documents %d through %d' % (i,j)
                for doc in results[i:j]:
                    DocumentCache.objects.get_cache(doc)

            sys.exit()

        elif o in ('-h', '--help'):
            usage()
            sys.exit()

    # Show the help screen if no commands given
    usage()
    sys.exit()
