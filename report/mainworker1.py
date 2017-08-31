# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from celery import Celery
from celery.schedules import crontab
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger

from datetime import date
import os

from report.conf import report_setting
from report.reportlist.models import ReportDownLoadsInfoTbl

import logging

# 引入需要调用的其他worker
from downloadworker2.py import downloadworker2

logger = logging.getLogger(__name__)

clogger = get_task_logger(__name__)

app = Celery('report', broker='amqp://guest@localhost')

@periodic_task(
    run_every=( crontab(minute = '*/10')),
    name="mainworker1",
    ignore_result=True
)

# 第一个启动的worker, 用来发起一些信息的查询获取任务, 然后再向相关的worker发送消息.
# 没有参数.
def mainworker1():
    # 下面的path 是将不同市场的公告列表存放在不同的路径中, 同时如果有下载的公告也存放在该路径下面的./report中
    pathmap = {"shmb":"0.shmb", "szmb":"1.szmb", "sme":"2.sme", "cyb":"3.cyb", "fund":"4.fund",
               "cnszbond":"5.cnszbond", "shbond":"6.shbond", "hkmb":"7.hkmb", "hkgem":"8.hkgem"}
    # 0. 获取路径定义
    desDir = report_setting.REPORT_DIR

    
    # 0. 获取时间信息, 以及构造文件名称的后缀
    dt = datetime.datetime.now()
    pathsuffix = dt.strftime('%Y')+"/"+dt.strftime('%m') + "/"+dt.strftime('%d')    # 比如 2017/04, 表示2017年4月的公告
    #suffix = dt.strftime('%Y%m%d')+ ("_1" if dt.hour < 17 else "_2")
    
    # 0.1 年月日字符串, 后面的循环中的getFileSuffix中会使用, 这儿只要计算一次即可, 为了提高一点儿性能而已
    datestr = dt.strftime('%Y') + dt.strftime('%m') + dt.strftime('%d')      # YYYYMMdd

    # 1. 获取需要下载的数据的url 列表
    reportUrls = ReportDownLoadsInfoTbl.objects.all()

    # 2. 然后逐条发送给下载worker: DownloadWorker2. 由该worker处理下载任务, 完成下载后发送消息给DispatchWorker3(调度Worker3)
    for report in reportUrls:
        url = report.url
        filename = report.filename
        memo = report.memo
        print(url)
        print(filename)
        print(memo)
        
        # 2.1 构造路径
        path = desDir + pathmap[memo]+ "/" + pathsuffix

        fileno, lastETag = getLstFileNo( path + "/" + filetype + datestr + ".lst" )
        reportlist = filetype + datestr + "_%3d.txt" % fileno     # 这个是需要下载的公告列表文件
        #         MSG0001: "MSG0001|url|Type|路径|下载后保存的文件名称及路径"
        msg = "MSG0001|"+url+"|"+report.filename+"|"+path+"|"+reportlist
        downloadworker2.delay(msg)

# 获取文件的编号, 查询 目标目录下面的同名公告列表.lst, 获取最后一个编号, 然后+1, 就是当前可用的编号, 每一次下载都要进行编号记录
# 例如:  cyb20170426.lst
# 参数:
#     path  : 列表文件所在的路径
#     filetype : 下载文件类型, 例如: "cyb", "shme"
#     datestr : 外部传入的日期字符串, "YYYYMMdd", 因为列表文件中需要这个字符串, 为了避免循环中多次计算, 从外部传入
# 说明:
#     列表文件内容格式如下:
#     1.cyb20170325_001.txt ETAG
#     2.cyb20170325_002.txt ETAG
#     3.cyb20170325_003.txt ETAG

def getLstFileNo( listfile ):
    
    # 0.1 如果列表文件不存在, 在编号就是1 ( 更新列表文件的内容是下载完成后再做, 这个时候会自动判断列表文件是否存在, 如果不存在就会创建 )
    if not os.access( listfile, os.F_OK ):   # 0.1 文件不存在, 则返回编号1,  容错处理1
        return (1,"")             

    if not os.path.isfile():   # 0.2 如果列表文件名称对应的是个文件夹, 则返回错误.  容错处理2
        return (-1,"")

    # 1. 处理列表文件, 获取最后一个编号
    fp = open( listfile, "r" )
    try:
        # 1.1 保存前一行的内容, 如果读取不到, 则说明到了文件末尾了, 那么上一次保存的内容就是最后一行的内容
        buf = fp.readline()
        if ( not buf ):  # 如果一行内容都没有的话, 说明是个空文件, 返回文件编号1
            fp.close()
            return (1,"")
        while( True ):
            curbuf = fp.readline()
            if ( not curbuf ):  # 如果到了文件结束就退出循环
                break
            buf = curbuf        # 更新buf 的内容, 文件没有结束, 继续读取

        # 1.2 解析最后一行的内容, 获取之前的最大文件编号, +1 后就是可用的下一个文件编号 ， 其实也就是第一个"."之前的数字
        fileno = int( buf.split(".")[0] ) + 1
        lastETag = buf.split(" ")[1]
        
    except IOError  as err:
        print( err )

    fp.close()
    return (fileno, lastETag)


str1 = "1"
d1 = 2

buf = str.format("%s = %d " % (str1, d1))
