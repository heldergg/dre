# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.transaction import commit_on_success

import datetime

##
# Exceptions
##

class TagError(Exception):
    pass

##
# Tags 
##

class TagManager(models.Manager):
    '''The Tag table has a complicated role in the site. All the table handling
    should be done throgh this manager in order to have consistency across the
    application.
    '''
    pass


class Tag(models.Model):
    user =  models.ForeignKey(User)
    timestamp = models.DateTimeField(default=datetime.datetime.now)

    name = models.CharField(max_length=128)
    public = models.BooleanField( default=True )
    note = models.TextField(max_length=5120, blank=True, null=True )
    color = models.IntegerField( default=0xFFFFFF )
    background = models.IntegerField( default=0x4060A2 )

    objects = TagManager()

    def __unicode__(self):
        return '<tag %s - %s - %s>' % (self.user.username,
                                       self.id,
                                       self.name)

    def style(self):
        return 'color:#%x;background:#%x;' % (self.color, self.background)

    class Meta:
        # Will raise an IntegrityError exception in the user tries to create 
        # two tags with the same name
        unique_together = ('user', 'name')

# Functions

@commit_on_success
def delete_tag(user, name, force=False):
    tag = Tag.objects.get(user=user, name=name)
    in_use = tag.objects.tag_in_use()

    if in_use and not force:
        raise TagError('Tag still in use, can\'t delete it.')
    
    if in_use and force: 
        # Get the objects where the tag is used 
        objects = TaggedItem.objects.filter( tag__exact = tag )
        for obj in objects:
            obj.delete()

    # Finally delete the damn tag
    tag.delete()


##
# Connect the tags to the objects
##

class TaggedItem(models.Model): 
    tag = models.ForeignKey(Tag)

    # Object:
    # https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return '<tagged item %s - %s>' % ( self.tag,
                             self.content_object )

    class Meta:
        unique_together = ('tag', 'content_type', 'object_id')


@commit_on_success
def del_tagged_item( tagged_item ): 
    # Detele the tag from the item
    tag = tagged_item.tag
    tagged_item.delete()

    # Check if there are any remaining objects tagged with this tag
    # if not, delete the tag
    remaining_tags = TaggedItem.objects.filter( tag__exact = tag )
    if not( remaining_tags ):
        tag.delete()
