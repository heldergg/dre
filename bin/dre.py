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

os.environ['DJANGO_SETTINGS_MODULE'] = 'dre_django.settings'

def usage():
    print '''Usage: %(script_name)s [options]\n
    Commands:
        -r
        --read_stats        Reads the stats from sitemeter

        -u <sitemeter_key>
        --read_single <sitemeter_key>
                            Reads the stats of a single blog

        -h
        --help              This help screen

    ''' % { 'script_name': sys.argv[0] }


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   'hru:v',
                                   ['help', 'read_stats','read_single=','verbose'])
    except getopt.GetoptError, err:
        print str(err)
        print
        usage()
        sys.exit(1)

    # Commands
    for o, a in opts:
        if o in ('-r', '--read_stats'):
            from webscraper.scrapstats import SitemeterScraper
            scraper = SitemeterScraper()
            scraper.run()
            sys.exit()

        elif o in ('-u', '--read_single'):
            from webscraper.scrapstats import SitemeterScraper
            sitemeter_key = a.strip()
            scraper = SitemeterScraper()
            scraper.read_blog(sitemeter_key)
            sys.exit()

        elif o in ('-h', '--help'):
            usage()
            sys.exit()

    # Show the help screen if no commands given
    usage()
    sys.exit()
