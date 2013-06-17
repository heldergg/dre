# -*- coding: utf-8 -*-

# Global imports:
from django.contrib.syndication.views import Feed
from django.core.urlresolvers import reverse
from django.conf import settings

# Local imports
from models import Document

##
# Latest
##

NUMBER_ENTRIES = getattr(settings, 'NUMBER_ENTRIES', 25)

class LatestEntriesFeed(Feed):
    title = 'Diários da República'
    link = "/latest/" # TODO: Make the view corresponding to this URL
    description = 'Modificações e novos documentos acrescentados ao site'

    def items(self):
        return Document.objects.order_by('-timestamp')[:NUMBER_ENTRIES]

    def item_title(self, item):
        return item.title()

    def item_description(self, item):
        return item.note_abrv()
