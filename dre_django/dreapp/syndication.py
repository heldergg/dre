# -*- coding: utf-8 -*-

# Global imports:
from datetime import datetime, time
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.conf import settings

# Local imports
import dreapp.index
from models import Document
from djapian.resultset import ResultSet


##
# Latest
##

NUMBER_ENTRIES = getattr(settings, 'NUMBER_ENTRIES', 25)
NUMBER_ENTRIES_QUERY = getattr(settings, 'NUMBER_ENTRIES_QUERY', 25)
SITE_URL = getattr(settings, 'SITE_URL', 'http://dre.tretas.org')

class LatestEntriesFeed(Feed):
    title = 'Diários da República'
    link = SITE_URL
    description = 'Modificações e novos documentos acrescentados ao site'
    ttl = 3600*12

    def get_object(self, request, *args, **kwargs):
        return request

    def items(self, request):
        query = request.GET.get('q', None)
        if not query:
            return Document.objects.order_by('-date')[:NUMBER_ENTRIES]
        else:
            # Return an rss resulting from a database query
            indexer = Document.indexer
            results = ResultSet(indexer, query, parse_query=True).order_by('-date')
            object_list = []
            for obj in results[:NUMBER_ENTRIES_QUERY]:
                object_list.append(obj.instance)

            return object_list

    def item_title(self, item):
        return item.title()

    def item_description(self, item):
        return item.note_abrv()

    def item_guid(self, item):
        return str(item.id)

    def item_author_name(self, item):
        return item.emiting_body

    def item_pubdate(self, item):
        return datetime.combine(item.date, time())
