# -*- coding: utf-8 -*-

'''
Convert PDF documents to txt
'''

from cStringIO import StringIO

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, PDFPageAggregator
from pdfminer.layout import LAParams
from pdfminer.layout import LTLine, LTRect, LTCurve, LTTextBoxHorizontal
from pdfminer.pdfpage import PDFPage

##
# Box operations
##

#         +----------+ (x1,y1)
#         |          |
#         |  box     |
#         |          |
# (x0,y0) +----------+

def box_intercepts(a_box, b_box):
    '''
    Box operations
    Checks if a_box intercepts b_box
    '''
    ax0, ay0, ax1, ay1 = a_box
    bx0, by0, bx1, by1 = b_box
    return ax0 <= bx1 and ax1 >= bx0 and ay0 <= by1 and ay1 >= by0

def box_envelope(a_box, b_box):
    '''
    Box operations
    Returns a box containing both a_box and b_box
    '''
    ax0, ay0, ax1, ay1 = a_box
    bx0, by0, bx1, by1 = b_box
    return min(ax0, bx0), min(ay0, by0), max(ax1, bx1), max(ay1, by1)

def box_spans_columns(page_box, box):
    '''
    Box operations
    Checks if box spans two columns in the page
    '''
    px0, py0, px1, py1 = page_box
    x0, y0, x1, y1 = box
    half_width = (px1 - px0)/2
    return x0 < half_width and x1 > half_width

def box_outside( page_box, box):
    '''
    Box operations
    Checks if a box has corners outside page_box
    '''
    px0, py0, px1, py1 = page_box
    x0, y0, x1, y1 = box
    return x0 < px0 or x1 > px1 or y0 < py0 or y1 > py1

##
# pdfminer reader
##

def convert_pdf_to_txt(path):
    '''
    Converts PDF to text using the pdfminer library
    '''
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    file_handle = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()

    for page in PDFPage.get_pages(
            file_handle,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=True):
        interpreter.process_page(page)

    text = retstr.getvalue()

    file_handle.close()
    device.close()
    retstr.close()
    return text

def convert_pdf_to_txt_layout(path, allowed_areas):
    '''
    Converts PDF to text using the pdfminer library
    '''
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    #device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    device = PDFPageAggregator(rsrcmgr, laparams=laparams)
    file_handle = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos = set()
    non_printable_re = re.compile(ur'(?:%s)' % '|'.join(
        [ chr(i) for i in range(1,31) if i != 10 ]))
    txt = []

    for page in PDFPage.get_pages(
            file_handle,
            pagenos,
            maxpages=maxpages,
            password=password,
            caching=caching,
            check_extractable=True):
        interpreter.process_page(page)
        layout = device.get_result()
        ignore = []

        # Identify areas to ignore
        for obj in layout:
            if ( obj.x0 < 0 or obj.y0 < 0 or
                 obj.x1 > page.mediabox[2] or
                 obj.y1 > page.mediabox[3]):
                continue
            if type(obj) == LTRect or type(obj) == LTCurve:
                expanded_region = False
                for i,region in enumerate(ignore):
                    if box_intercepts(obj.bbox, region):
                        ignore[i] = box_envelope(obj.bbox, region)
                        expanded_region = True
                if not expanded_region:
                    ignore.append(obj.bbox)

        # Gather text from non ignored regions
        for obj in layout:
            # Print only Horizontal Text Boxes
            if type(obj) != LTTextBoxHorizontal:
                continue

            # Checks if object is within allowed areas
            if allowed_areas:
                ignore_obj = reduce( lambda x,y: x and y,
                        [box_outside(area, obj.bbox) for area in allowed_areas])
                if ignore_obj:
                    continue

            # Checks if object is within ignored areas
            if ignore:
                ignore_obj = reduce( lambda x,y: x or y,
                        [box_intercepts(obj.bbox, region) for region in ignore])
                if ignore_obj:
                    continue

            obj_txt = obj.get_text()
            obj_txt = non_printable_re.sub( '', obj_txt)
            obj_txt = obj_txt.strip()

            txt.append(u' '.join(obj_txt.split('\n')))

    text = u'\n'.join(txt)

    file_handle.close()
    device.close()
    retstr.close()
    return text
