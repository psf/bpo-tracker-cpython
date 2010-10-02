# Django mappings for roundup tables
from django.db import models

class Session(models.Model):
    session_key = models.CharField(primary_key=True, max_length=255)
    session_value = models.TextField()
    class Meta:
        db_table = 'sessions'

class User(models.Model):
    _username = models.CharField()
    _realname = models.CharField()
    _address = models.CharField()
    class Meta:
        db_table = '_user'

class File(models.Model):
    _creator = models.IntegerField()
    _creation = models.DateTimeField()
    _branch = models.CharField()
    _revision = models.CharField()
    _patchset = models.CharField()
    class Meta:
        db_table = '_file'

class RoundupIssue(models.Model):
    _creator = models.IntegerField()
    _creation = models.DateTimeField()
    _status = models.IntegerField()
    class Meta:
        db_table = '_issue'
