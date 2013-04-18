# -*- coding: utf-8 -*-

import os
import re

from datetime import datetime
from django.db import models
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist

from bookmarksapp.models import Bookmark
from tagsapp.models import TaggedItem
from notesapp.models import Note

# select distinct doc_type from dreapp_document order by doc_type;
doc_type = (
    'ACÓRDÃO',
    'ACORDO',
    'ACTA',
    'ALVARÁ',
    'ALVARÁ-EXTRACTO',
    'ANÚNCIO',
    'ASSENTO',
    'AUTORIZAÇÃO',
    'AVISO',
    'AVISO-EXTRACTO',
    'CARTA DE CONFIRMAÇÃO E RATIFICAÇÃO DE CONVENÇÃO INTERNACIONAL',
    'CARTA DE LEI',
    'COMUNICAÇÃO DE RENÚNCIA',
    'CONTA',
    'CONTRATO',
    'CONTRATO-EXTRACTO',
    'CONVÉNIO',
    'DECLARAÇÃO',
    'DECLARAÇÃO DE DÍVIDA',
    'DECLARAÇÃO DE RECTIFICAÇÃO',
    'DECRETO',
    'DECRETO LEGISLATIVO REGIONAL',
    'DECRETO LEI',
    'DECRETO REGIONAL',
    'DECRETO REGULAMENTAR',
    'DECRETO REGULAMENTAR REGIONAL',
    'DELIBERAÇÃO',
    'DELIBERAÇÃO-EXTRACTO',
    'DESPACHO',
    'DESPACHO CONJUNTO',
    'DESPACHO-EXTRACTO',
    'DESPACHO MINISTERIAL',
    'DESPACHO NORMATIVO',
    'DESPACHO ORIENTADOR',
    'DESPACHO RECTIFICATIVO',
    'DESPACHO REGULADOR',
    'DIRECTIVA CONTABILÍSTICA',
    'EDITAL',
    'EXTRACTO',
    'INSTRUÇÃO',
    'INSTRUÇÕES',
    'JURISPRUDÊNCIA',
    'LEI',
    'LEI CONSTITUCIONAL',
    'LEI ORGÂNICA',
    'LISTAGEM',
    'LISTA RECTIFICATIVA',
    'LOUVOR',
    'MAPA',
    'MAPA OFICIAL',
    'MOÇÃO',
    'MOÇÃO DE CONFIANÇA',
    'NÃO ESPECIFICADO',
    'NORMA',
    'PARECER',
    'PORTARIA',
    'PORTARIA-EXTRACTO',
    'PROCESSO',
    'PROTOCOLO',
    'RECOMENDAÇÃO',
    'RECTIFICAÇÃO',
    'REGIMENTO',
    'REGULAMENTO',
    'REGULAMENTO INTERNO',
    'RELATÓRIO',
    'RESOLUÇÃO',
    'RESOLUÇÃO DA ASSEMBLEIA NACIONAL',
)


class Document(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    doc_type = models.CharField(max_length=64)

    number = models.CharField(max_length=32)
    emiting_body = models.CharField(max_length=512)
    source = models.CharField(max_length=128)
    dre_key = models.CharField(max_length=32)
    in_force = models.BooleanField(default=True)
    conditional = models.BooleanField(default=False)
    processing = models.BooleanField(default=False)
    date = models.DateField()

    notes = models.CharField(max_length=20480)

    plain_text = models.URLField()
    dre_pdf = models.URLField()
    pdf_error = models.BooleanField(default=False)

    timestamp = models.DateTimeField(default=datetime.now())

    # Reverse generic relations
    bookmarks = generic.GenericRelation(Bookmark)
    tags = generic.GenericRelation(TaggedItem)
    user_notes = generic.GenericRelation(Note)

    def bookmark(self, user):
        '''Return the bookmark associated to this document if it exists'''
        try:
            content_type = ContentType.objects.get_for_model(Document)
            return Bookmark.objects.get(user=user, object_id=self.id,
                    content_type = content_type )
        except ObjectDoesNotExist:
            return False

    # Display in lists
    def note_abrv(self):
        if len(self.notes) < 512:
            return self.notes
        else:
            return self.notes[:512] + ' (...)'

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
        # TODO: substitute this regexes for compiled regexes

        command = '/usr/bin/pdftohtml -i -nodrm  -noframes -stdout %s' % self.plain_pdf_filename()
        html = os.popen(command).read()
        html = html[html.find('<BODY bgcolor="#A0A0A0" vlink="blue" link="blue">')+50:-17]
        html = html.replace('&nbsp;', ' ').replace('<hr>','')
        html = re.sub( r' *<br>', '<br>', html)
        html = re.sub( r'([:.;])<br>', r'\1\n<p style="text-align:justify;">', html)
        html = re.sub( r'([0-9a-zA-Z,])<br>', r'\1 ', html)
        html = re.sub( r'<b>(.*?)</b><br>', r'<p><strong>\1</strong></p><p style="text-align:justify;">', html)

        # NOTE: we have some badly formed links on the original PDFs. Sometimes
        # we have latin-1 characters on the 'href' attribute of the link. This
        # originates problems when displaying the document since we're going
        # to have a document with two encodings (utf-8 and latin-1).
        html = re.sub( r'<a href.*?>(.*?)</a>', r'\1', html)
        html = html.replace('</b><br>','</b><br><p>')

        # "Decreto-Lei" recognition
        html = re.sub( r'((Decreto-Lei|Lei)(?: | n.º )([\-a-zA-Z0-9]+/[a-zA-Z0-9]+))',
                       r'<a href="/?q=tipo:\2 número:\3">\1</a>', html)

        return html

    def plain_txt(self):
        '''Converts the plain_pdf pdf to txt'''
        filename = self.plain_pdf_filename()
        if os.path.exists(filename):
            command = '/usr/bin/pdftotext -htmlmeta -layout %s -' % filename
            return os.popen(command).read()
        else:
            return ''

class FailedDoc(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    tries = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=datetime.now())
