# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db import transaction
from django.utils import timezone

##
# Exceptions
##

class TagError(Exception):
    pass

##
# Tags
##

class TagManager(models.Manager):
    def user_tags( self, user, public_only ):
        '''Returns the tags available to a given user'''
        if public_only:
            return super(TagManager, self).get_query_set().filter(
                user__exact = user).filter(
                public__exact = True).order_by('name')
        else:
            return super(TagManager, self).get_query_set().filter(
                user__exact = user).order_by('name')

class Tag(models.Model):
    objects = TagManager()

    user =  models.ForeignKey(User)
    timestamp = models.DateTimeField(default=timezone.now)

    name = models.CharField(max_length=128)
    public = models.BooleanField( default=True )
    color = models.IntegerField( default=0xFFFFFF )
    background = models.IntegerField( default=0x4060A2 )

    def __unicode__(self):
        return '<tag %s - %s - %s>' % (self.user.username,
                                       self.id,
                                       self.name)

    def style(self):
        return 'color:#%06x;background:#%06x;' % (self.color, self.background)

    class Meta:
        # Will raise an IntegrityError exception in the user tries to create
        # two tags with the same name
        unique_together = ('user', 'name')

# Functions

@transaction.atomic
def delete_tag(tag):
    # Get the objects where the tag is used
    tagged_list = TaggedItem.objects.filter( tag__exact = tag )
    for obj in tagged_list:
        # delete t
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
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return '<tagged item %s - %s>' % ( self.tag,
                             self.content_object )

    class Meta:
        unique_together = ('tag', 'content_type', 'object_id')


@transaction.atomic
def del_tagged_item( tagged_item ):
    # Detele the tag from the item
    tag = tagged_item.tag
    tagged_item.delete()

    # Check if there are any remaining objects tagged with this tag
    # if not, delete the tag
    remaining_tags = TaggedItem.objects.filter( tag__exact = tag )
    if not( remaining_tags ):
        tag.delete()
