# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
import datetime

##
#  Notes
##

class Note(models.Model):
    user =  models.ForeignKey(User)
    timestamp = models.DateTimeField(default=datetime.datetime.now)
    public = models.BooleanField( default=True )

    txt = models.TextField(max_length = 1024*20)

    # Object:
    # https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def html(self):
        return '<p>%(txt)s</p><p>(Nota %(public)s)</p>' % {
            'txt': self.txt,
            'public': 'p&uacute;blica' if self.public else 'privada' }

    def __unicode__(self):
        return 'Note: %s - %s - model: %s' % (self.user.username, 
                                        self.id, 
                                        self.content_type.name)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

