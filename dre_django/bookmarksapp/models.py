# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
import datetime

##
#  Bookmarks
##

class Bookmark(models.Model):
    user =  models.ForeignKey(User)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    public = models.BooleanField( default=True )

    # Object:
    # https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return '<bm: %s - %s - model: %s>' % (self.user.username,
                                        self.id,
                                        self.content_type.name)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')
