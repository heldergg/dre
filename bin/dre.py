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
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

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

        --create_cache YYYY₁-MM₁-DD₁:YYYY₂-MM₂-DD₂
                            Creates (or updates) the cache for the documents
                            in the date range
        --create_cache document_id
                            Updates the cache for the document with id
                            document_id

        -h
        --help              This help screen

    Options:
        Filtering options:

        These options filter the documents to be read. Use these options with
        "--read_date" or "--read_range".

        --no_series_1
        --no_series_2       Ignore documents from series one or two

        --filter_type <type>
                            Process only documents of this type
        --filter_number <number>
                            Process only documents with this number

        Update mode, re-reads the documents:

        The following options will enable the update mode. All these
        options are false by default. You have to pick what you intend
        to update. Use these options with "--read_date" or "--read_range".

        --update_metadata   doc name, number, date, etc
        --update_notes
        --update_digesto
        --update_inforce
        --save_pdf

        NOTE: on every update option if a new document is found it will be
        retrieved completely independent of the value of this update options.

    ''' % { 'script_name': sys.argv[0] }

##
# Utils

def create_update_cache(doc):
    logger.debug('CACHEPDF to %d %s %s %s' % (doc.id,
        doc.date, doc.doc_type, doc.number))
    cache = DocumentCache.objects.get_cache_object(doc)
    cache.build_cache()
    try:
        change = Change()
        change.object = doc
        change.action = 'edit'
        change.save()
    except IntegrityError:
        logger.error('CACHEPDF Djapian change already '
            'sheduled for doc id=%d' % doc.id)

if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                    'hr:dv',
                                   ['help',
                                    'read_date=', 'read_range=',
                                    'dump',
                                    'create_cache=',
                                    'no_series_1', 'no_series_2',
                                    'filter_type=', 'filter_number=',
                                    'update_metadata','update_notes',
                                    'update_digesto', 'update_inforce',
                                    'save_pdf',
                                   ])
    except getopt.GetoptError, err:
        print str(err)
        print
        usage()
        sys.exit(1)

    # Defaults
    filter_doc= {} # Document filtering options
    filter_dr= {}  # Journal filtering options
    options= {}    # Document reading options

    # Options
    options['update_notes'] = False
    options['update_metadata'] = False
    options['update_digesto'] = False
    options['update_inforce'] = False
    options['save_pdf'] = False

    for o, a in opts:
        # Filter options:
        if o == '--no_series_1':
            filter_dr['no_series_1'] = True
        elif o == '--no_series_2':
            filter_dr['no_series_2'] = True
        elif o == '--filter_type':
            filter_doc['doc_type'] = a.lower()
        elif o == '--filter_number':
            filter_doc['number'] = a.lower()
        # Update options:
        elif o == '--update_notes':
            options['update'] = True
            options['update_notes'] = True
        elif o == '--update_metadata':
            options['update'] = True
            options['update_metadata'] = True
        elif o == '--update_digesto':
            options['update'] = True
            options['update_digesto'] = True
        elif o == '--update_inforce':
            options['update'] = True
            options['update_inforce'] = True
        elif o == '--save_pdf':
            options['update'] = True
            options['save_pdf'] = True

    # Commands
    for o, a in opts:
        if o in ('-r', '--read_date'):
            import datetime
            from drescraperv3 import DREReadDay, DREDocSave
            from drescraperv3 import DREDuplicateError

            try:
                date = datetime.datetime.strptime( a, '%Y-%m-%d' )
            except ValueError:
                print 'A date in ISO format must be passed to this command'
                sys.exit(1)

            day = DREReadDay(date)
            for doc in day.read_index(filter_dr, filter_doc):
                update_obj = DREDocSave(doc, options)
                try:
                    update_obj.save_doc()
                except DREDuplicateError:
                    pass

            sys.exit()

        elif o == '--read_range':
            import datetime
            import time
            from drescraperv3 import DREReadDay, DREDocSave
            from drescraperv3 import DREDuplicateError

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
                day = DREReadDay(date)
                for doc in day.read_index(filter_dr, filter_doc):
                    update_obj = DREDocSave(doc, options)
                    try:
                        update_obj.save_doc()
                    except DREDuplicateError:
                        pass
                date += datetime.timedelta(1)

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


        elif o == '--create_cache':
            import datetime
            from dreapp.models import Document, DocumentCache
            from djapian.models import Change
            from drelog import logger
            page_size = 1000
            doc_id = None
            try:
                date1, date2 = a.split(':')
            except ValueError:
                try:
                    doc_id = int(a)
                except ValueError:
                    print ('A date range in the format '
                           'YYYY₁-MM₁-DD₁:YYYY₂-MM₂-DD₂ or a document id '
                           'is needed.')
                    sys.exit()
            if doc_id:
                try:
                    doc = Document.objects.get(id=doc_id)
                except ObjectDoesNotExist:
                    print 'Doc with id %d does not exist' % doc_id
                    sys.exit()
                create_update_cache(doc)
            else:
                try:
                    date1 = datetime.datetime.strptime( date1, '%Y-%m-%d' )
                    date2 = datetime.datetime.strptime( date2, '%Y-%m-%d' )
                except ValueError:
                   print 'The dates provided must be in ISO format.'
                   sys.exit(1)
                results = Document.objects.filter(date__gte = date1
                        ).filter(date__lte = date2)
                for i in range(0,results.count(), page_size):
                    j = i + page_size
                    print '* Processing documents %d through %d' % (i,j)
                    for doc in results[i:j]:
                        create_update_cache(doc)
            sys.exit()


        elif o in ('-h', '--help'):
            usage()
            sys.exit()

    # Show the help screen if no commands given
    usage()
    sys.exit()
