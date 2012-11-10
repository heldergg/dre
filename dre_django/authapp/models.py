# -*- coding: utf-8 -*-

from django.db import models

class AccessAttempt(models.Model):
    ip_address = models.IPAddressField('IP Address')
    failures = models.PositiveIntegerField('Failed Logins', default=0)
