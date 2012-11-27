# -*- coding: utf-8 -*-

'''Tags forms'''

from django import forms

from tagsapp.models import Tag

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag 
        fields = ('name', 'public', 'note', 'color', 'background' )
