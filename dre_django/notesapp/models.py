# -*- coding: utf-8 -*-

try:
    import markdown
    md = True
except ImportError:
    md = False

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

##
#  Notes
##

class Note(models.Model):
    user =  models.ForeignKey(User)
    timestamp = models.DateTimeField(default=timezone.now)
    public = models.BooleanField( default=True )

    txt = models.TextField(max_length = 1024*20)

    # Object:
    # https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def html(self):
        if md:
            note_html = markdown.markdown(self.txt,
                    safe_mode='remove',
                    output_format='html',
                    extensions=['tables', 'footnotes'])
        else:
            note_html = self.txt

        return note_html

    def __unicode__(self):
        return 'Note: %s - %s - model: %s' % (self.user.username,
                                        self.id,
                                        self.content_type.name)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

