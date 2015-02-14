# -*- coding: utf-8 -*-

'''
Read apache logs in the format:

"%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-agent}i\""

and copy them to a database.
'''

##
## Imports
##

import re
from datetime import datetime

from django.conf import settings
from django.db.models import Max
from django.db import transaction

from statsapp.models import LogLine

##
## Settings
##

APACHE_LOG = getattr(settings, 'APACHE_LOG', None)
PAGE_SIZE  = getattr(settings, 'PAGE_SIZE', 100000)

##
## Regex
##

logline_re = re.compile(
    r'^(?P<remote_host>\d+\.\d+\.\d+\.\d+) - '
    r'(?P<remote_user>[a-zA-Z0-9\-"]+) '
    r'\[(?P<timestamp>.*)?\] '
    r'"(?P<request_type>[A-Z"]+) (?P<request_path>.+) (?P<request_proto>[^ ]+)" '
    r'(?P<response_status>\d+) '
    r'(?P<response_bytes>(?:-|\d+)) '
    r'"(?P<request_referer>.*)?" '
    r'"(?P<request_useragent>.*)?"$'
    )

##
## Read the log
##

class LogReader(object):
    def __init__(self, apache_log = APACHE_LOG):
        self.apache_log = apache_log
        self.page_number = 1


    def last_log(self):
        return LogLine.objects.all().aggregate(Max('timestamp'))['timestamp__max']


    def save_line(self, m, ts):
        ln = LogLine()

        request_path = m.group('request_path')
        if len(request_path) > 8190:
            request_path = request_path[:8190]

        ln.timestamp = ts
        ln.remote_host = m.group('remote_host')
        ln.remote_user = m.group('remote_user')
        ln.request_type = m.group('request_type')
        ln.request_path = request_path
        ln.request_proto = m.group('request_proto')
        ln.response_status = int(m.group('response_status'))
        ln.response_bytes = int(m.group('response_bytes')) if m.group('response_bytes') != '-' else 0
        ln.request_referer = m.group('request_referer')
        ln.request_useragent = m.group('request_useragent')

        ln.save()


    def save_page( self, page ):
        print "Page ", self.page_number
        self.page_number += 1

        with transaction.atomic():
            for ln in page:
                m = logline_re.match(ln)
                ts = datetime.strptime( m.group('timestamp').split(' ')[0],
                        '%d/%b/%Y:%H:%M:%S')

                if ts > self.last:
                    self.save_line(m, ts)


    def reader(self):
        last_log = self.last_log()
        self.last = last_log if last_log else datetime(1980,1,1)
        page = []
        lines = 0

        with open(self.apache_log,'r') as log:
            try:
                for ln in log:
                    page.append(ln)
                    lines += 1
                    if not lines % PAGE_SIZE:
                        self.save_page( page )
                        del page
                        page = []
                self.save_page( page )
            except:
                print ln
                raise


    def run(self):
        self.reader()
