# -*- coding: utf-8 -*-

from django.contrib import sitemaps
from django.core.urlresolvers import reverse

class StaticViewSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['about', 'help', 'top', 'last', 'today_results']

    def location(self, item):
        return reverse(item)


