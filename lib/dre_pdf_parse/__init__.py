# -*- coding: utf-8 -*-

'''
Convert DRE PDF documents to html
'''

##
# Imports
##

from pdf_to_txt import convert_pdf_to_txt
from pdf_to_txt import convert_pdf_to_txt_layout
from tender_parser import parse_tender
from generic_parser import parse_generic_document

import dreapp

##
# Pdf parser
##

class ParsePdf(object):
    def __init__(self, doc):
        self.filename = doc.dre_pdf_filename()
        self.doc = doc

    def get_html(self):
        raise NotImplementedError('This is an abstract method.')

    def run(self):
        return self.get_html()

class ParseTenderPdf(ParsePdf):
    def get_html(self):
        txt = convert_pdf_to_txt(self.filename).decode('utf-8')
        txt = txt[txt.find(self.doc.doc_type):]
        return parse_tender.run(txt)

class ParseGenericPdf(ParsePdf):
    def next_doc(self):
        '''
        Get the next document after the current one. This is necessary to
        properly cut the pdf.
        Note, this means that we can only get the text representation after
        getting the complete journal.
        '''
        cur_timestamp = self.doc.timestamp
        cur_dr_number = self.doc.dr_number
        cur_series = self.doc.series
        Document = dreapp.models.Document
        next_document = Document.objects.filter(dr_number__exact=cur_dr_number
                ).filter(series__exact=cur_series
                ).filter(timestamp__gt=cur_timestamp
                ).order_by('timestamp')
        return next_document[0] if next_document else None

    def cut_out_doc(self, txt):
        next_doc=self.next_doc()
        if next_doc:
            next_doc=u'%s n.\xba %s' % (next_doc.doc_type, next_doc.number)
        cur_doc=u'%s n.\xba %s' % (self.doc.doc_type, self.doc.number)
        if next_doc:
            return txt[txt.find(cur_doc):txt.find(next_doc)]
        else:
            return txt[txt.find(cur_doc):]

    def get_html(self):
        allowed_areas = (
                ( 45, 60, 295, 780),
                (297, 60, 550, 780),
                )
        txt = convert_pdf_to_txt_layout(self.filename, allowed_areas)
        txt = self.cut_out_doc(txt)
        return parse_generic_document.run(txt)

def parse_pdf(doc):
    # Public tenders:
    if (doc.doc_type.lower() == u'Anúncio de Procedimento'.lower() or
            doc.doc_type.lower() == u'Aviso de prorrogação de prazo'.lower() or
            doc.doc_type.lower() == u'Declaração de retificação de anúncio'.lower() or
            doc.doc_type.lower() == u'Anúncio de concurso urgente'.lower()):
        return ParseTenderPdf(doc).run()

    # Generic documents:
    return ParseGenericPdf(doc).run()
