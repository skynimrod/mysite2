# -*-  coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from celery import Celery
from celery.schedules import crontab
from celery.task.schedules import crontab
from celeryt.decorators import periodic_task
from celery.utils.log import get_task_logger

from datetime import date

from report.conf import report_settting
from report.reportlist.models import ReportDownLoadsInfoTbl, ReportListTbl
from report.reportlist.downloadReportList import getReportList

from utils.url_tools import MultThreadDownload

from utils.db_tools import execSQL, querySQL

import logging

logger = logging.getLogger(__name__)

clogger = get_task_logger(__name__)

app = Celery('report', broker='amqp://guest@localhost')

@periodic_task(
    run_every=( crontab(minute = '*/10')),
    name="downloadworker2",
    ignore_result=True
)

# 下载worker. 
# 说明:
#     1.  只处理下载请求, 处理结果发送给 dispatchworker3(调度worker).
#     2.  只有收到消息才进行处理, 否则不处理.
#     3.  没有任何业务逻辑, 只简单处理下载任务.
#     4.  下载后的文件路径及文件名称都在消息体中.
#     5. 处理的消息类型有: (消息格式基本一致, 区别仅仅是消息编号, 表示不同的处理方式, 便于下一步的处理)
#         MSG0001: "MSG0001|url|Type|路径|下载后保存的文件名称及路径", type = "cyb"
#         Msg0002: "MSG0002|url|Type|路径|下载后保存的文件名称|日期", type = "report"
#       其中, MSG0001下载的是公告列表, MSG0002下载的是公告.
def downloadworker2( msg ):

    # 0. 拆分消息体, 按分隔符"|" 进行拆分
    buf = msg.split("|")

    MSGID, url, filetype, path, filename = buf[0], buf[1], buf[2], buf[3], buf[4]

    # 1. 下载文件
    filename += suffix+'.txt'
    #ret = Downloads(url, path, filename )    # 返回结果是个Tuple (str, http.client.HTTPMessage)
    ret = MultThreadDownload(url, path, filename )    # 返回结果是个ETag 或""

    
    

