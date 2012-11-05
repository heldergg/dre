# -*- coding: utf-8 -*-

'''Xapian index for this application

To rebuild the index:
$ ./manage.py index --rebuild

To use the index shell:
$ ./manage.py indexshell
>>> use 0.1.0
>>> query asdkjnd as
'''

from djapian import space, Indexer
from djapian.resultset import ResultSet
from dreapp.models import Document
import xapian

class DocumentIndexer(Indexer):
    stemming_lang_accessor = 'portuguese'
    fields = [ 'doc_type', 'number', 'emiting_body', 'source', 'notes', 'plain_txt']
    tags = [
        ('notes', 'notes'),
        ('date', 'date_to_index'),
        ('year', 'year'),
        ('month', 'month'),
        ('day', 'day'),
        ('type', 'doc_type'),
        ('number','number'),
        ('who','emiting_body'),
        ('source','source')
        ]
    aliases = {
        'notes': 'notas',
        'date':'data',
        'year':'ano',
        'month':'mês',
        'day':'dia',
        'type':'tipo',
        'number':'número',
        'who': 'quem',
        'source':'fonte',
        }


    def related(self, article):
        PUNCTUATION = ",. \n\t\\\"'][#*:()"

        words = article.split()
        words = list(set([ word.strip(PUNCTUATION) for word in words ]))

        query = xapian.Query( xapian.Query.OP_ELITE_SET, words)

        return self.search( query, parse_query = False).prefetch()

    def relevant(self, rsetids, word_number = 40):
        database = self._db.open()
        enquire = xapian.Enquire(database)
        rset = xapian.RSet()

        if  isinstance(rsetids, list):
            for docid in rsetids:
                rset.add_document(docid)
        else:
            rset.add_document(rsetids)

        eset = enquire.get_eset(word_number, rset)

        query = xapian.Query( xapian.Query.OP_OR,
                    [ eset_item.term for eset_item in eset ])

        return self.search( query, parse_query = False).prefetch()

space.add_index(Document, DocumentIndexer, attach_as='indexer')
