from datetime import datetime
from django.db import models

class Document(models.Model):
    claint = models.IntegerField() # dre.pt site id
    doc_type = models.CharField(max_length=32)

    number = models.CharField(max_length=16)
    emiting_body = models.CharField(max_length=128)
    source = models.CharField(max_length=128)
    dre_key = models.CharField(max_length=32)
    date = models.DateField()

    notes = models.CharField(max_length=1024)

    plain_text = models.URLField()
    dre_pdf = models.URLField()

    timestamp = models.DateTimeField(default=datetime.now())
