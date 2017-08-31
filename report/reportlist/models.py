# -*-  coding: utf-8  -*-

from django.db import models

from django.utils import timezone
import datetime

# 公告过滤关键字列表  ReportFilterTbl
# key   是需要过滤得关键字
# flag  是否需要过滤
class ReportFilterTbl( models.Model ):
    key = models.CharField('关键字', max_length=20, unique = True )
    flag = models.BooleanField('是否过滤', default=False )

# 公告关键字组合表   ReportKeySetTbl

# 新增股份表    NewCapitalTbl

# 公告下载信息表  ReportDownLoadsInfoTbl

from utils.url_tools import isValidURL

class ReportDownLoadsInfoTbl(models.Model):
    url = models.CharField('下载地址',max_length=255)
    filename = models.CharField('文件名称', max_length = 10, blank = True, null = True )
    memo = models.CharField('说明',max_length = 255, blank = True, null = True)

    
    def was_valid_url(self):
        return isValidURL(url)


# 公告信息表   ReportListTbl   每年都单独维护一个表, 结构等同于ReportListTbl, 名称为Report_List_YYYY_Tbl
# 说明:
#    reporturl 是缺少前缀 http://www.cninfo.com.cn, 使用的时候要添加
#    reporttype 一般是pdf, 这个预留, 暂时不用, 缺省pdf
#    
class ReportListTbl(models.Model):
    stockcode   = models.CharField('股票代码',  max_length = 6, blank = False )
    reporturl   = models.CharField('公告地址',  max_length = 255, blank = False, unique = True )
    reportname  = models.CharField('公告名称',  max_length = 255, blank = False )

    PDF     = 'pdf'
    TXT     = 'txt'
    HTML    = 'html'
    REPORT_TYPE_CHOICES = ( (PDF, 'pdf file'), (TXT, 'txt file'), (HTML, 'html file'), )
    reporttype  = models.CharField('公告类型',  max_length = 4, blank = False,
                                   choices = REPORT_TYPE_CHOICES, default= PDF, )
    
    flag1       = models.CharField('待用' ,    max_length = 6, blank = False )
    releaseddate = models.CharField('发布日期', max_length = 10, blank = False )
    releasedtime = models.CharField('发布时间', max_length = 18, blank = False )

class ReportList_2016_Tbl(models.Model):
    stockcode   = models.CharField('股票代码',  max_length = 6, blank = False )
    reporturl   = models.CharField('公告地址',  max_length = 255, blank = False, unique = True )
    reportname  = models.CharField('公告名称',  max_length = 255, blank = False )
    PDF     = 'pdf'
    TXT     = 'txt'
    HTML    = 'html'
    REPORT_TYPE_CHOICES = ( (PDF, 'pdf file'), (TXT, 'txt file'), (HTML, 'html file'), )
    reporttype  = models.CharField('公告类型',  max_length = 4, blank = False,
                                   choices = REPORT_TYPE_CHOICES, default= PDF, )
    flag1       = models.CharField('待用' ,    max_length = 6, blank = False )
    releaseddate = models.CharField('发布日期', max_length = 10, blank = False )
    releasedtime = models.CharField('发布时间', max_length = 18, blank = False )
