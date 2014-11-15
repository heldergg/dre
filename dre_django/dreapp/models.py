# -*- coding: utf-8 -*-

import os
import re
import cgi

import datetime
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
from dre_convertpdf import DREPDFReader

# Needed for dates < 1899 (read note bellow)
MONTHS = [ u'Janeiro', u'Fevereiro', u'Março', u'Abril', u'Maio',
    u'Junho', u'Julho', u'Agosto', u'Setembro', u'Outubro',
    u'Novembro', u'Dezembro' ]

# New site date

NEWSITE = datetime.date(2014,9,17)

##
# Regular expressions - used to detect references to other documents
##

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

doc_type_str = '|'.join([ xi.lower().replace(' ','(?:\s+|-)')
    for xi in sorted(doc_type, key=len, reverse=True) ])


doc_ref_dtype = ur'(?P<doc_type>%s)\s+' % doc_type_str

doc_ref_mid   = ur'(?P<mid>número\s+|n\.º\s+|n\.\s+|nº\s+|n\s+)'

doc_ref_number = ur'(?P<number>(?:\d+\s\d+|(?:[\-A-Z0-9]+)(?:/[\-A-Z0-9]+)*))'

doc_ref_date  = ur'(?P<date>,\s+de\s+[0-9]+\s+de\s+(?:%(months)s)(?:\s+de\s+\d{2,4})?)?' % {
        'months': '|'.join(MONTHS), }


doc_ref_re_str = doc_ref_dtype + doc_ref_mid + doc_ref_number + doc_ref_date

## Plural

doc_type_plural = (
        u'Leis',
        u'Decretos-Lei',
        u'Decretos-Leis',
        u'Portarias',
        u'Despachos',
        )

doc_type_relation = {
        u'leis': u'Lei',
        u'decretos-lei': u'Decreto-Lei',
        u'decretos-leis': u'Decreto-Lei',
        u'portarias': u'Portaria',
        u'despachos': u'Despacho',
        }

doc_type_str_plural = '|'.join([ xi.lower()
    for xi in sorted(doc_type_plural, key=len, reverse=True)])

doc_ref_dtype_plural = ur'(%s)\s+' % doc_type_str_plural

doc_ref_mid_plural = ur'(?:números|n\.os|n\.º|n\.|n)\s+'

doc_ref_number_plural = ur'(?:\d+\s\d+|[\-A-Z0-9]+(?:/[\-A-Z0-9]+)*)'

doc_ref_date_plural  = ur'(?:,\s+de\s+[0-9]+\s+de\s+(?:%(months)s)(?:\s+de\s+\d{2,4})?)?' % {
        'months': '|'.join(MONTHS), }

doc_ref_re_str_plural = ( doc_ref_dtype_plural + doc_ref_mid_plural +
        r'((?:' + doc_ref_number_plural +  doc_ref_date_plural + r',\s+)+' +
        r'e\s+' + doc_ref_number_plural + doc_ref_date_plural ) + r')'


## Compile the regexes

FLAGS_RE = re.UNICODE | re.IGNORECASE | re.MULTILINE

doc_ref_re = re.compile( doc_ref_re_str, FLAGS_RE )
doc_ref_plural_re = re.compile( doc_ref_re_str_plural, FLAGS_RE )

# regex used to transform the user's search queries
doc_ref_optimize_re = re.compile( ur'(?P<doc_type>%s)(?:\s+número\s+|\s+n\.º\s+|\s+n\.\s+|\s+nº\s+|\s+n\s+|\s+)?(?P<number>[/\-a-zA-Z0-9]+)' % doc_type_str, flags= re.UNICODE)

##
## Utility functions
##

def title( st, exceptions = ['a','o','e','de','da','do']):
    wl = []
    for word in re.sub(r'\s+',' ', st.lower()).split(' '):
        if word not in exceptions:
            wl.append(word.capitalize())
        else:
            wl.append(word)
    return ' '.join(wl)


##
## Models
##

class Document(models.Model):
    '''
    This table stores the document's metadata.

    We used several sources for the document's text:

    i)   Initially we used the text extracted from the 'texto integral' PDFs;
    ii)  Then we've found out a way of extracting the text from the site itself
         using some special crafted URLs. The text is stored on the
         DocumentText table;
    iii) The third source source was used when the site was upgraded. This time
         the source is the DR's PDF it self. The results are not as good but
         good enough to index the document. An auxiliary table is needed to
         store infromation about the next document on the DR, this is used to
         know where the document ends within the DR. The table is named
         DocumentNext.

    In any case the html presented is generated by a method of this table.
    '''

    claint = models.IntegerField(unique=True) # dre.pt site id
    doc_type = models.CharField(max_length=128)

    number = models.CharField(max_length=32)
    emiting_body = models.CharField(max_length=512)
    source = models.CharField(max_length=128)
    dre_key = models.CharField(max_length=32)
    dr_number = models.CharField(max_length=16, default='')
    series  = models.IntegerField(default=1)
    in_force = models.BooleanField(default=True)
    conditional = models.BooleanField(default=False)
    processing = models.BooleanField(default=False)
    date = models.DateField()

    notes = models.CharField(max_length=20480)

    plain_text = models.URLField()
    dre_pdf = models.URLField()
    pdf_error = models.BooleanField(default=False)

    timestamp = models.DateTimeField(default=datetime.datetime.now())

    # Reverse generic relations
    bookmarks = generic.GenericRelation(Bookmark)
    tags = generic.GenericRelation(TaggedItem)
    user_notes = generic.GenericRelation(Note)

    # Connection to other documents
    connects_to = models.ManyToManyField('self',  symmetrical=False)

    def out_links(self):
        return self.connects_to.all().order_by('date')

    def in_links(self):
        return self.document_set.all().order_by('date')

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

    def note_escaped(self):
        return cgi.escape(self.note_abrv(), quote = True)

    def c_emitting(self):
        '''Comma separated emitting body list'''
        return ', '.join( [ e.strip().title() for e in self.emiting_body.split(';') ])

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

    def dre_pdf_filename(self):
        return os.path.join(self.archive_dir(), 'dre-%s.pdf' % self.claint)

    # Representation
    def plain_html(self):
        '''Converts the plain_pdf pdf to html'''
        return DocumentCache.objects.get_cache(self)

    def plain_txt(self):
        '''Converts the plain_pdf pdf to txt'''
        filename = self.plain_pdf_filename()
        try:
            doc_text = DocumentText.objects.get( document = self, text_type = 0)
        except ObjectDoesNotExist:
            doc_text = None

        if doc_text:
            # Get the text from the integral text
            text = doc_text.text
            text = re.sub(r'<.*?>',r'', text)
            text = text.replace('TEXTO :','')

        elif os.path.exists(filename):
            # Get the text from the plain text pdf
            command = '/usr/bin/pdftotext -htmlmeta -layout %s -' % filename
            text = os.popen(command).read()

        elif self.date > NEWSITE:
            # Create cache from the dre_pdf file, this is needed for the new
            # site
            importer = DREPDFReader(self)
            text = importer.plain_txt()

        else:
            # No text
            text = ''

        return text

    def has_text(self):
        try:
            doc_text = DocumentText.objects.get( document = self, text_type = 0)
        except ObjectDoesNotExist:
            doc_text = None

        if self.plain_text or doc_text:
            return True

        if self.date > NEWSITE:
            return True

        return False

    def title(self):
        # Note: strftime requires years greater than 1899, even though we do not
        # deal with year arithmetic in this method we are forced to find the
        # full month name ourselves.
        return u'%s %s, de %d de %s' % (
                    title(self.doc_type),
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

    def __unicode__(self):
        return self.title()

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
    timestamp = models.DateTimeField(default=datetime.datetime.now())

    objects = CacheManager()

    def get_doc_from_title(self, doc_type, number):
        document = Document.objects.filter(
            Q(doc_type__iexact = doc_type.replace(' ','-') ) |
            Q(doc_type__iexact = doc_type.replace('-',' ') )
            ).filter(number__iexact = number.replace(' ',''))
        if len(document) == 1:
            if self.document != document[0]:
                self.document.connects_to.add(document[0])
            return document[0]
        return None

    def make_links(self,  match ):
        doc_type = match.groupdict()['doc_type']
        number = match.groupdict()['number']
        date = match.groupdict()['date']

        # Try to get the referred document from the cache
        doc = self.doc_cache.get( doc_type+number, None)
        # If the doc isn't on the cache, try to get it from the database
        if not doc:
            doc = self.get_doc_from_title(doc_type, number)

        if doc:
            url      = doc.get_absolute_url()
            title    = cgi.escape(doc.note_abrv(), quote = True)
            self.doc_cache[ doc_type+number ] = doc
        else:
            url = u'/?q=tipo:%s número:%s' % ( doc_type, number.replace(' ',''))
            title = u'Não temos sumário disponível'
        link_txt = u'%s %s%s' % (doc_type, number, date if date else '')

        return '<a href="%s" title="%s">%s</a>' % (url, title, link_txt)

    def make_links_plural(self, match ):
        g = match.groups()

        doc_type = doc_type_relation[g[0].lower()]
        n = [ xi.strip() for xi in g[1].replace(' e ',' ').split(',') ]
        numbers = zip(n[::2],n[1::2])

        links = []

        for number, date in numbers:
            # Try to get the referred document from the cache
            doc = self.doc_cache.get( doc_type+number, None)
            # If the doc isn't on the cache, try to get it from the database
            if not doc:
                doc = self.get_doc_from_title(doc_type, number)

            if doc:
                url      = doc.get_absolute_url()
                title    = cgi.escape(doc.note_abrv(), quote = True)
                self.doc_cache[ doc_type+number ] = doc
            else:
                url = u'/?q=tipo:%s número:%s' % ( doc_type, number.replace(' ',''))
                title = u'Não temos sumário disponível'
            link_txt = u'%s, %s' % (number, date if date else '')

            links.append( '<a href="%s" title="%s">%s</a>' % (url, title, link_txt) )


        links_txt = ', '.join(links[:-1]) + u' e %s' % links[-1]

        return u'%s %s' % (g[0], links_txt )

    def build_cache_from_pdf(self, filename):
        # Convert the PDF to html
        # TODO: substitute this regexes for compiled regexes
        command = '/usr/bin/pdftohtml -i -nodrm  -noframes -stdout %s' % (
                filename )
        html = os.popen(command).read()
        html = html[html.find('<BODY bgcolor="#A0A0A0" vlink="blue" link="blue">')+50:-17]
        html = html.replace('&nbsp;', ' ').replace('<hr>','').replace('&#160;', ' ')
        html = html.replace('<br/>','<br>')

        # The following will not work on python 2.6.6 (it works fine on 2.7.5):
        # html = re.sub( r'^(.{0,50})<br>\n', r'<p><strong>\1</strong></p>\n', html, flags=re.MULTILINE)
        # Instead the following must be used:
        html = '\n'.join([ '<p><strong>%s</strong></p>' % l[:-4]
                           if l[-4:] == '<br>' and len(l) < 50 else l
                           for l in html.split('\n') ])
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

        return html

    def build_cache(self):
        # Rebuild the cache
        self.version = DOCUMENT_VERSION
        self.timestamp = datetime.datetime.now()
        filename = self.document.plain_pdf_filename()
        try:
            doc_text = DocumentText.objects.get( document = self.document, text_type = 0)
        except ObjectDoesNotExist:
            doc_text = None

        if doc_text:
            # Build the html from the integral text
            html = doc_text.text
            html = re.sub( r'(Artigo \d+\..)\n',r'<strong>\1</strong>', html)
            html = re.sub( u'(CAPÍTULO [IVXLD]+)\n',r'<strong>\1</strong>', html)
            html = re.sub( u'(SECÇÃO [IVXLD]+)\n',r'<strong>\1</strong>', html)
            html = html.replace('TEXTO :','')
            html = html.replace('eurlex.asp', 'http://www.dre.pt/cgi/eurlex.asp')
        elif os.path.exists(filename):
            # Build the html from the plain text html
            html = self.build_cache_from_pdf(filename)
            html = unicode(html,'utf-8','ignore')
        elif self.document.date > NEWSITE:
            # Create cache from the dre_pdf file, this is needed for the new
            # site
            importer = DREPDFReader(self.document)
            html = importer.run()
        else:
            # No text to represent
            self._html = ''
            self.save()
            html = ''

        # Recognize other document names and link to them:
        self.doc_cache = {}
        self.document.connects_to.clear()
        html = doc_ref_re.sub( self.make_links, html )
        html = doc_ref_plural_re.sub( self.make_links_plural , html )

        self._html = html
        self.save()

    def get_html(self):
        '''This method does the following:
        * Build the html cache for the plan text representation of the document;
        * Creates a list of documents connected to the current document
        '''
        if self.version < DOCUMENT_VERSION or settings.DEBUG:
            self.build_cache()

        return self._html

    html = property(get_html)


class FailedDoc(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    tries = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=datetime.datetime.now())

TEXT_DOC        = 0
TEXT_SUMMARY_PT = 1
TEXT_SUMMARY_EN = 2

class DocumentText(models.Model):
    '''
    This table is used to store raw html retrieved from dre.pt
    '''
    document  = models.ForeignKey(Document)
    timestamp = models.DateTimeField(default = datetime.datetime.now())
    text_url  = models.URLField()
    text_type = models.IntegerField(default=0)

    text = models.TextField()

    class Meta:
        unique_together = ('document', 'text_type')

class DocumentNext(models.Model):
    '''
    This table is used to store the next document type and number. This
    information allows us to frame the document within a PDF with multiple
    documents snippets mixed together.

    This is only used for documents beginning the 18th September, 2014,
    when the source site was upgraded.
    '''

    document  = models.ForeignKey(Document, unique=True )
    timestamp = models.DateTimeField(default = datetime.datetime.now())

    doc_type = models.CharField(max_length=128)
    number = models.CharField(max_length=32)
