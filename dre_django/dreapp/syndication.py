# -*- coding: utf-8 -*-

# Global imports:
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse

# Local imports
from models import Document

##
# Latest
##

class LatestEntriesFeed(Feed):
    title = 'Diários da República'
    link = "/latest/" # TODO: Make the view corresponding to this URL
    description = 'Modificações e novos documentos acrescentados ao site'

    def items(self):
        return Document.objects.order_by('-timestamp')[:50]

    def item_title(self, item):
        return item.title()

    def item_description(self, item):
        return item.note_abrv()
