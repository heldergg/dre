from datetime import datetime
from django.db import models

class Document(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    doc_type = models.CharField(max_length=64)

    number = models.CharField(max_length=32)
    emiting_body = models.CharField(max_length=512)
    source = models.CharField(max_length=128)
    dre_key = models.CharField(max_length=32)
    in_force = models.BooleanField(default=True)
    conditional = models.BooleanField(default=False)
    date = models.DateField()

    notes = models.CharField(max_length=20480)

    plain_text = models.URLField()
    dre_pdf = models.URLField()
    pdf_error = models.BooleanField(default=False)

    timestamp = models.DateTimeField(default=datetime.now())

    def date_to_index (self):
        return self.date.strftime('%Y%m%d')

    def note_abrv(self):
        if len(self.notes) < 512:
            return self.notes
        else:
            return self.notes[:512]


class FailedDoc(models.Model):
    claint = models.IntegerField(unique=True) # dre.pt site id
    tries = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=datetime.now())
