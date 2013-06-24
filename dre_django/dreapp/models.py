# -*- coding: utf-8 -*-

import os
import re
import cgi

from datetime import datetime
from django.conf import settings
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q

from bookmarksapp.models import Bookmark
from tagsapp.models import TaggedItem
from notesapp.models import Note

# Needed for dates < 1899 (read note bellow)
MONTHS = [ u'Janeiro', u'Fevereiro', u'Março', u'Abril', u'Maio',
    u'Junho', u'Julho', u'Agosto', u'Setembro', u'Outubro',
    u'Novembro', u'Dezembro' ]

# select distinct doc_type from dreapp_document order by doc_type;
doc_type = (
    u'ACÓRDÃO',
    u'ACORDO',
    u'ACTA',
    u'ALVARÁ',
    u'ALVARÁ-EXTRACTO',
    u'ANÚNCIO',
    u'ASSENTO',
    u'AUTORIZAÇÃO',
    u'AVISO',
    u'AVISO-EXTRACTO',
    u'CARTA DE CONFIRMAÇÃO E RATIFICAÇÃO DE CONVENÇÃO INTERNACIONAL',
    u'CARTA DE LEI',
    u'COMUNICAÇÃO DE RENÚNCIA',
    u'CONTA',
    u'CONTRATO',
    u'CONTRATO-EXTRACTO',
    u'CONVÉNIO',
    u'DECLARAÇÃO',
    u'DECLARAÇÃO DE DÍVIDA',
    u'DECLARAÇÃO DE RECTIFICAÇÃO',
    u'DECRETO',
    u'DECRETO LEGISLATIVO REGIONAL',
    u'DECRETO LEI',
    u'DECRETO REGIONAL',
    u'DECRETO REGULAMENTAR',
    u'DECRETO REGULAMENTAR REGIONAL',
    u'DELIBERAÇÃO',
    u'DELIBERAÇÃO-EXTRACTO',
    u'DESPACHO',
    u'DESPACHO CONJUNTO',
    u'DESPACHO-EXTRACTO',
    u'DESPACHO MINISTERIAL',
    u'DESPACHO NORMATIVO',
    u'DESPACHO ORIENTADOR',
    u'DESPACHO RECTIFICATIVO',
    u'DESPACHO REGULADOR',
    u'DIRECTIVA CONTABILÍSTICA',
    u'EDITAL',
    u'EXTRACTO',
    u'INSTRUÇÃO',
    u'INSTRUÇÕES',
    u'JURISPRUDÊNCIA',
    u'LEI',
    u'LEI CONSTITUCIONAL',
    u'LEI ORGÂNICA',
    u'LISTAGEM',
    u'LISTA RECTIFICATIVA',
    u'LOUVOR',
    u'MAPA',
    u'MAPA OFICIAL',
    u'MOÇÃO',
    u'MOÇÃO DE CONFIANÇA',
    u'NÃO ESPECIFICADO',
    u'NORMA',
    u'PARECER',
    u'PORTARIA',
    u'PORTARIA-EXTRACTO',
    u'PROCESSO',
    u'PROTOCOLO',
    u'RECOMENDAÇÃO',
    u'RECTIFICAÇÃO',
    u'REGIMENTO',
    u'REGULAMENTO',
    u'REGULAMENTO INTERNO',
    u'RELATÓRIO',
    u'RESOLUÇÃO',
    u'RESOLUÇÃO DA ASSEMBLEIA NACIONAL',
)

space = ur'\s+'

doc_type_str = '|'.join([ xi.lower().replace(' ','(?:%(space)s|-)' % { 'space': space }) for xi in sorted(doc_type, key=len, reverse=True) ])

doc_ref_dtype = ur'(?P<doc_type>%(doc_type)s)%(space)s' % {
        'doc_type': doc_type_str,
        'space': space }
doc_ref_mid   = ur'(?P<mid>número\s+|n\.º\s+|n\.\s+|nº\s+|n\s+)'
doc_ref_number= ur'(?P<number>(?:(?:[\-A-Z0-9]+)(?:/[\-A-Z0-9]+)*|\d+\s\d+|\d+))'
doc_ref_date  = ur'(?P<date>,%(space)sde%(space)s[0-9]+%(space)sde%(space)s(?:%(months)s))?' % {
        'months': '|'.join(MONTHS),
        'space': space }

doc_ref_re_str = doc_ref_dtype + doc_ref_mid + doc_ref_number + doc_ref_date

FLAGS_RE = re.UNICODE | re.IGNORECASE | re.MULTILINE

doc_ref_re = re.compile( doc_ref_re_str, FLAGS_RE )

doc_ref_optimize_re = re.compile( ur'(?P<doc_type>%s)(?:\s+número\s+|\s+n\.º\s+|\s+n\.\s+|\s+nº\s+|\s+n\s+|\s+)?(?P<number>[/\-a-zA-Z0-9]+)' % doc_type_str, flags= re.UNICODE)

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

    # Representation
    def plain_html(self):
        '''Converts the plain_pdf pdf to html'''
        return DocumentCache.objects.get_cache(self)

    def plain_txt(self):
        '''Converts the plain_pdf pdf to txt'''
        filename = self.plain_pdf_filename()
        if os.path.exists(filename):
            command = '/usr/bin/pdftotext -htmlmeta -layout %s -' % filename
            return os.popen(command).read()
        else:
            return ''

    def title(self):
        # Note: strftime requires years greater than 1899, even though we do not
        # deal with year arithmetic in this method we are forced to find the
        # full month name ourselves.
        return u'%s %s, de %d de %s' % (
                    self.doc_type.title(),
                    self.number,
                    self.day(),
                    MONTHS[self.month()-1] )

    def dict_repr(self):
        '''Dictionary representation'''

        return {
            'claint'       : self.claint,
            'doc_type'     : self.doc_type,
            'number'       : self.number,
            'emiting_body' : self.emiting_body.split(';'),
            'source'       : self.source,
            'dre_key'      : self.dre_key,
            'in_force'     : self.in_force,
            'conditional'  : self.conditional,
            'processing'   : self.processing,
            'date'         : self.date.isoformat(),
            'notes'        : self.notes,
            'plain_text'   : self.plain_text,
            'dre_pdf'      : self.dre_pdf,
            'pdf_error'    : self.pdf_error,
            'timestamp'    : self.timestamp.isoformat(sep=' '),
        }

    # Other
    def get_absolute_url(self):
        return reverse('document_display', kwargs={ 'docid':self.id })

DOCUMENT_VERSION = getattr(settings, 'DOCUMENT_VERSION', 1)

class CacheManager(models.Manager):
    def get_cache(self, document):
        try:
            cache = super(CacheManager, self).get_query_set(
                    ).get(document=document)
        except ObjectDoesNotExist:
            cache = DocumentCache()
            cache.document = document
            cache.version = 0
            cache._html = ''
            cache.save()

        return cache.html


class DocumentCache(models.Model):
    '''This table is used to store a cached html representation of the
    Document's 'plain_pdf' file. The 'version' field must be equal or greater
    than the settings variable DOCUMENT_VERSION, this way, if it's necessary to
    invalidate the Document cache we only have to increase the DOCUMENT_VERSION
    value.
    '''
    document = models.ForeignKey(Document, unique=True)
    version  = models.IntegerField()
    _html    = models.TextField()
    timestamp = models.DateTimeField(default=datetime.now())

    objects = CacheManager()

    def get_doc_from_title(self, doc_type, number):
        document = Document.objects.filter(
            Q(doc_type__iexact = doc_type.replace(' ','-') ) |
            Q(doc_type__iexact = doc_type.replace('-',' ') )
            ).filter(number__iexact = number.replace(' ',''))
        if len(document) == 1:
            return document[0]
        return None

    def make_links(self,  match ):
        doc_type = match.groupdict()['doc_type']
        number = match.groupdict()['number']
        date = match.groupdict()['date']
        doc = self.get_doc_from_title(doc_type, number)
        if doc:
            url      = doc.get_absolute_url()
            title    = cgi.escape(doc.note_abrv(), quote = True)
        else:
            url = u'/?q=tipo:%s número:%s' % ( doc_type, number.replace(' ',''))
            title = u'Não temos sumário disponível'
        link_txt = u'%s %s%s' % (doc_type, number, date if date else '')

        return '<a href="%s" title="%s">%s</a>' % (url, title, link_txt)

    def get_html(self):
        if self.version >= DOCUMENT_VERSION and not settings.DEBUG:
            return self._html

        # Rebuild the cache
        self.version = DOCUMENT_VERSION
        self.timestamp = datetime.now()
        filename = self.document.plain_pdf_filename()

        if not os.path.exists(filename):
            # No text to represent
            self._html = ''
            self.save()
            return ''

        # Convert the PDF to html
        # TODO: substitute this regexes for compiled regexes

        command = '/usr/bin/pdftohtml -i -nodrm  -noframes -stdout %s' % (
                filename )
        html = os.popen(command).read()
        html = html[html.find('<BODY bgcolor="#A0A0A0" vlink="blue" link="blue">')+50:-17]
        html = html.replace('&nbsp;', ' ').replace('<hr>','').replace('&#160;', ' ')
        html = html.replace('<br/>','<br>')
        html = re.sub( r'\s+<br>', '<br>', html)
        html = re.sub( r'([:.;])<br>', r'\1\n<p style="text-align:justify;">', html)
        html = re.sub( r'<b>(.*?)</b><br>', r'<p><strong>\1</strong></p><p style="text-align:justify;">', html)
        # html = re.sub( r'([0-9a-zA-Z, ])<br>', r'\1 ', html)
        html = html.replace('<br>', ' ')

        # NOTE: we have some badly formed links on the original PDFs. Sometimes
        # we have latin-1 characters on the 'href' attribute of the link. This
        # originates problems when displaying the document since we're going
        # to have a document with two encodings (utf-8 and latin-1).
        html = re.sub( r'<a href.*?>(.*?)</a>', r'\1', html)
        html = html.replace('</b><br>','</b><br><p>')

        # Recognize other document names and link to them:
        html = doc_ref_re.sub( self.make_links, unicode(html,'utf-8','ignore') )

        self._html = html
        self.save()
        return html

    html = property(get_html)


class FailedDoc(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    tries = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=datetime.now())
