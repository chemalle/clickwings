from django.contrib import admin

# Register your models here.

from accounting.models import Accounting


class AccountingAdmin(admin.ModelAdmin):
    list_display =["__str__","company","conta_devedora","conta_credora","amount","date"]
    search_fields = ["conta_devedora","date","conta_devedora","conta_credora","amount"]
    list_filter = ["conta_devedora", "conta_credora","date"]
    list_editable = ["amount"]
    class Meta:
        model = Accounting

admin.site.register(Accounting, AccountingAdmin)


# company = models.CharField(max_length=200)
# history = models.CharField(max_length=200)
# date = models.DateTimeField()
# debit = models.CharField(max_length=100)
# credit = models.CharField(max_length=100)
# amount = models.DecimalField(default=0.0, max_digits=8, decimal_places=2)
# conta_devedora = models.CharField(max_length=200)
# conta_credora = models.CharField(max_length=200)
# objects = models.Manager()
# pdobjects = DataFrameManager()  # Pandas-Enabled Manager
