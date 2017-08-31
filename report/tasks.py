from __future__ import absolute_import, unicode_literals

from celery import Celery
from celery.schedules import crontab
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger

from datetime import date

from report.conf import report_setting
from report.reportlist.models import ReportDownLoadsInfoTbl, ReportListTbl
from report.reportlist.downloadReportList import getReportList

from report.reportlist.parseReportList import parseReportList
from report.views import buildStockBriefInfoTbl

from utils.url_tools import Downloads

from utils.db_tools import execSQL, querySQL

import logging

logger = logging.getLogger(__name__)

clogger = get_task_logger(__name__)

app = Celery('report', broker='amqp://guest@localhost//')

@periodic_task(
    run_every=( crontab(minute='*/10')),
    name="updatereporttask",
    ignore_result=True
)
def updatereporttask():
    desDir = report_setting.REPORT_DIR

    reportUrls = ReportDownLoadsInfoTbl.objects.all()
    #clogger( reportUrls )
    for report in reportUrls:
        clogger.info( report.url )
    getReportList( reportUrls, desDir )

    clogger.info("Download report data finished. now process the data... Please don't shutdown!!! ")

    # 0. 清空 最新公告的信息内容 report_reportlisttbl
    sqlstr = 'delete from report_reportlisttbl'
    execSQL( sqlstr )

    reportset = ['shmb', 'szse', 'sme', 'cyb' ]

    d1 = date.today()
    datestr = d1.strftime( '%Y%m%d' )
    pathstr = desDir + '/' + datestr
        
    for item in reportset :
        filename = pathstr + '/' + item +datestr+'_1.txt'   
        li = parseReportList( filename )

        filename = pathstr + '/' + item +datestr+'_2.txt'   
        li = parseReportList( filename )

        # 仅处理最新的公告
        buildStockBriefInfoTbl( 'report_reportlisttbl' )  
                
    
    return('**adamstask  Test**')
