# -*-   coding: utf-8   -*-

from django.db import models

from django.utils import timezone
import datetime
from datetime import date

# 只有添加了下面这一句, 系统才可以找到并处理reportlist下面的models.py
from report.reportlist.models import ReportListTbl  


#=========================================

# 1. 汉字拼音表 HZpy_Tbl
class hzpyTbl(models.Model):
    py = models.CharField('拼音',max_length=6)
    hz = models.CharField('汉字', max_length=2, blank = True, null = True )

# 2. 节假日信息表 HolidayTbl
class HolidayTbl(models.Model):
    start = models.DateField('起始日期', blank=False )
    end = models.DateField('结束日期', blank=False )
    memo = models.CharField('节假日说明', max_length=20)

# 3. 地区信息表  AreaTbl

# 3. 证监会行业分类表  CSRCIndustryTbl

# 4. 中证行业分类表    CSIIndustryTbl

# 5. 证券信息表 SecurityTbl  主要用于标记分类，计算指数等

# 股票简明信息表  StockBriefInfoTbl
class StockBriefInfoTbl(models.Model):
    stockcode = models.CharField('股票代码', max_length=6)
    stockname = models.CharField('股票简称', max_length = 8)
    stockpy = models.CharField('股票拼音', max_length = 6)   # 为了防止*st 类型的可能会超长
    industry = models.CharField('所属行业', max_length = 20, blank = True, null = True )  #
    subjects = models.CharField('题材概念板块', max_length = 40, blank = True, null = True )

# 股票主力详细息系表     StockDayInfoTbl


# 股票交易数据月统计表  StockStatisticMonthTbl

# 不可用股票代码表  NoUsedStockTbl

# 股票周交易数据表

# 股票月交易数据表

# 股票财务数据表

#. 股票动态行情表

# 指数信息表

# 系统筛选股票信息表  SysStockFilterTbl

# 用户自选股记录表   SelfFilterTbl
# 
class selfSelectedTbl(models.Model):
    username  = models.CharField('用户名', max_length=20, blank=False )
    stockcode =models.CharField('股票代码', max_length=6, blank=False)
    groupname =models.CharField('自选股编组',max_length=20, blank=True, null = True)

# 实时监控信息表

# ============================

# 用户信息表 CustomerUserTbl

# 用户访问记录表  VisitedURLsTbl

# 用户访问次数表  VisitCounterTbl

# 黑名单表   BlackIPTbl

# 用户缴费记录表

# 用户登录历史表

# =========================

# 股评信息表

#============

# 股票位置信息表   StockPosTbl

# 股票分红信息表

# 退市、停牌股票表  StockDelistingTbl

# ===================

# 公告精选信息表  ReportPickedTbl

