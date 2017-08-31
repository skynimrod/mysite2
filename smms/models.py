#  -*- coding: utf-8  -*-

from django.db import models

import django.utils import timezone
import datetime


# 1. 汉字拼音表 HZpy_Tbl
class hzpyTbl():
    py = models.CharField()

# 2. 节假日信息表 HolidayTbl

# 3. 地区信息表  AreaTbl

# 3. 证监会行业分类表  CSRCIndustryTbl

# 4. 中证行业分类表    CSIIndustryTbl

# 5. 证券信息表 SecurityTbl  主要用于标记分类，计算指数等

# 股票基本信息表  StockBaseInfoTbl
class StockBaseInfoTbl(models.Model):
    stockcode = models.CharField('股票代码',max_length=6)

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

# 公告信息表   ReportListedTbl

# 公告关键字列表  ReportKeysTbl

# 公告关键字组合表   ReportKeySetTbl

# 新增股份表    NewCapitalTbl

# 公告下载信息表  ReportDownLoadsInfoTbl
class ReportDownLoadsInfoTbl(models.Model):
    url = models.CharField('下载地址',max_length=255)
    filename = models.CharField('文件名称', max_length = 4, blank = True )
    memo = models.CharField('说明',max_length = 255， blank = True)

    
