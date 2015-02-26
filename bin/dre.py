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

import django
django.setup()

def usage():
    print '''Usage: %(script_name)s [options]\n
    Commands:
        -r YYYY-MM-DD
        --read_date YYYY-MM-DD
                            Read the DRs from a given date

        --read_range YYYY₁-MM₁-DD₁:YYYY₂-MM₂-DD₂
                            Read the DRs from in a given date range

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
                                    'hr:dvc',
                                   ['help',
                                    'read_date=', 'read_range=',
                                    'dump', 'update_cache',
                                   ])
    except getopt.GetoptError, err:
        print str(err)
        print
        usage()
        sys.exit(1)

    # Commands
    for o, a in opts:
        if o in ('-r', '--read_date'):
            import datetime
            from drescraperv2 import DREReader

            try:
                date = datetime.datetime.strptime( a, '%Y-%m-%d' )
            except ValueError:
                print 'A date in ISO format must be passed to this command'
                sys.exit(1)

            dr = DREReader( date )
            dr.read_index()
            dr.save_doc_list()

            sys.exit()

        elif o == '--read_range':
            import datetime
            import time
            from drescraperv2 import DREReader

            try:
                date1, date2 = a.split(':')
            except ValueError:
                print 'A date range in the format YYYY₁-MM₁-DD₁:YYYY₂-MM₂-DD₂ is needed.'
                sys.exit()

            try:
                date1 = datetime.datetime.strptime( date1, '%Y-%m-%d' )
                date2 = datetime.datetime.strptime( date2, '%Y-%m-%d' )
            except ValueError:
               print 'The dates provided must be in ISO format.'
               sys.exit(1)

            date = date1
            while date <= date2:
                dr = DREReader( date )
                dr.read_index()
                dr.save_doc_list()
                date += datetime.timedelta(1)
                time.sleep( 5 )

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
