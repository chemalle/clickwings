from django.db import models
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.db import models
from django.forms import ModelForm
from django_pandas.managers import DataFrameManager



# Create your models here.

class Accounting(models.Model):
    company = models.CharField(max_length=200)
    history = models.CharField(max_length=200)
    date = models.DateTimeField()
    debit = models.CharField(max_length=100)
    credit = models.CharField(max_length=100)
    amount = models.DecimalField(default=0.0, max_digits=20, decimal_places=2)
    conta_devedora = models.CharField(max_length=200)
    conta_credora = models.CharField(max_length=200)
    objects = models.Manager()
    pdobjects = DataFrameManager()  # Pandas-Enabled Manager



    def __str__(self):
        return self.history
