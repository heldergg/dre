# -*- coding: utf-8 -*-

'''Notes forms'''

from django import forms

from notesapp.models import Notes 

class NoteForm(forms.Form):
    txt = forms.CharField(
        required=False,
        max_length=20480,
        widget=forms.Textarea )
