from django.contrib import admin

# Register your models here.
from guardian.admin import GuardedModelAdmin

from report.reportlist.models import ReportDownLoadsInfoTbl

#class ReportDownLoadsInfoTblAdmin(GuardedModelAdmin):
    
admin.site.register(ReportDownLoadsInfoTbl)
