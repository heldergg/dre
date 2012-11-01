# -*- coding: utf-8 -*-

"""Project forms"""

from django import forms

class QueryForm(forms.Form):
    """
    General Xapian Query
    """
    q = forms.CharField(
        required=True,
        max_length=1000,)

