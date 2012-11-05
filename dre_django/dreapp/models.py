# -*- coding: utf-8 -*-

import os

from datetime import datetime
from django.db import models
from django.conf import settings


class Document(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    doc_type = models.CharField(max_length=64)

    number = models.CharField(max_length=32)
    emiting_body = models.CharField(max_length=512)
    source = models.CharField(max_length=128)
    dre_key = models.CharField(max_length=32)
    in_force = models.BooleanField(default=True)
    conditional = models.BooleanField(default=False)
    date = models.DateField()

    notes = models.CharField(max_length=20480)

    plain_text = models.URLField()
    dre_pdf = models.URLField()
    pdf_error = models.BooleanField(default=False)

    timestamp = models.DateTimeField(default=datetime.now())

    # Display in lists
    def note_abrv(self):
        if len(self.notes) < 512:
            return self.notes
        else:
            return self.notes[:512]

    # Date methods
    def year(self):
        return self.date.year

    def month(self):
        return self.date.month

    def day(self):
        return self.date.day

    def date_to_index (self):
        return '%d%02d%02d' % ( 
            self.date.year,
            self.date.month,
            self.date.day, )

    # File methods
    def archive_dir(self):
        return  os.path.join( settings.ARCHIVEDIR,
                            '%d' % self.year(),
                            '%02d' % self.month(),
                            '%02d' % self.day() )

    def plain_pdf_filename(self):
        return os.path.join(self.archive_dir(), 'plain-%s.pdf' % self.claint) 

    def plain_html(self):
        '''Converts the plain_pdf pdf to html''' 
        command = 'pdftohtml -i -nodrm  -noframes -stdout %s' % self.plain_pdf_filename()
        html = os.popen(command).read()
        html = html[html.find('<BODY bgcolor="#A0A0A0" vlink="blue" link="blue">')+50:-17]

        return html
         
    def plain_txt(self):
        '''Converts the plain_pdf pdf to txt''' 
        filename = self.plain_pdf_filename()
        if os.path.exists(filename):
            command = 'pdftotext -htmlmeta -layout %s -' % filename 
            return os.popen(command).read()
        else:
            return ''

class FailedDoc(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    tries = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=datetime.now())
