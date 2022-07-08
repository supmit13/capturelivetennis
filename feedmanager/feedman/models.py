from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Feed(models.Model):
    feedtitle = models.CharField(max_length=500, null=False, blank=False, default='Missing')
    feedeventteam1 = models.CharField(max_length=300, null=False, blank=False, default='')
    feedeventteam2 = models.CharField(max_length=300, null=False, blank=False, default='')
    feedstart = models.DateTimeField(auto_now=True)
    feedend = models.DateTimeField(blank=True, null=True, default='0001-01-01 00:00:01')
    eventtype = models.CharField(max_length=250, null=False, blank=True, default='')
    eventresult = models.CharField(max_length=500, null=True, blank=False, default=None) # Tie would be specified as 'tie'. Otherwise, team names (name(s) of player(s)) would be specified. Default is None.
    feedstatus = models.CharField(max_length=100, null=False, blank=False, default='live')
    feedpath = models.CharField(max_length=500, null=False, blank=False, default='')
    deleted = models.BooleanField(default=False)
    updatetime = models.DateTimeField(auto_now_add=True)
    updateuser = models.ForeignKey(User, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Feeds Table"
        db_table = 'feedman_feeds'


