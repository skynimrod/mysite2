from django.shortcuts import render

import conf
import models.ReportDownLoadsInfoTbl
# Create your views here.




# 下载公告列表
def DownloadReportListView():
    desDir = conf.REPORT_DIR

    template_name = 'report/download.html'
    context_object_name = 'report_list_RawData'
    

    
