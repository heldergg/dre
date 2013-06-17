# -*- coding: utf-8 -*-

# Global Imports
from django.contrib import sitemaps
from django.core.urlresolvers import reverse

# Local Imports
from dreapp.models import Document

class DocumentSitemap(sitemaps.Sitemap):
    changefreq = "yearly"
    priority = 0.5

    def items(self):
        return Document.objects.all()

    def lastmod(self, obj):
        return obj.timestamp
