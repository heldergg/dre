# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
import datetime

##
# Tags 
##

class Tag(models.Model):
    user =  models.ForeignKey(User)
    timestamp = models.DateTimeField(default=datetime.datetime.now)

    name = models.CharField(max_length=128)
    public = models.BooleanField( default=True )
    note = models.TextField(max_length=5120, blank=True, null=True )
    color = models.IntegerField( default=0xFFFFFF )
    background = models.IntegerField( default=0x444444 )


    def __unicode__(self):
        return 'tag %s - %s - %s' % (self.user.username,
                                     self.id,
                                     self.name)

class TaggedItem(models.Model): 
    tag = models.ForeignKey(Tag)

    # Object:
    # https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return '%s - %s' % ( self.tag,
                             self.content_object )

    class Meta:
        unique_together = ('tag', 'content_type', 'object_id')


