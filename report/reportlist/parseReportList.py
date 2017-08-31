# -*-  coding: utf-8  -*-

import os
import re

import logging

logger = logging.getLogger(__name__)


#from utils.date_tools import isValidDateStr
from utils.base_tools import dupClassDefine, addClassDefine
from utils.db_tools import execSQL

# 处理指定日期时间段之内的公告列表
# reportDir        存放公告列表文件的路径
# startDate        起始日期(包括该日期)
# endDate          结束时间(包括该日期)
# 返回值:
#       False       处理失败
def parseReportLists( reportDir, start, end ):
    # 1. 检查日期是否是合法的( countDays() 中已经检查了, 不用单独检查)
    #if ( !isValidDate(end) || !isValidDateStr(end) )
    #    return False

    # 2. 不用检查目标路径是否有 公告列表文件, 没有就不处理而已

    # 3. 获取日期间隔
    #days = countDays( start, end ) + 1

    #if ( days == 0 ):  # 如果countDays返回-1， 由于+1了, 所以这儿判断的是0
    #    return False

    return True


# 处理指定日期的公告列表
# parseReportList( filename )
# 参数说明:
#     filename       公告列表文件. 内容是公告列表
# 实现说明:
#   1.放弃遍历一遍来获取公告数据的做法, 这个方法虽然效率较高, 但是可维护性可读性较差
#     使用正则表达式来处理, 采用2次遍历的方法, 第一次遍历获取单条公告数据,
#     第二次逐个公告数据进行解析.
#   2.处理单条公告信息的时候, 用dict 来实现switch的功能
#   3.数据持久化
#     这儿有个容错处理, 容许多个reportlist_YYY_tbl 的访问. 一般情况下不会发生同一文件
#     数据多个年份的公告的现象, 这儿的处理仅仅是个容错.
#     用一个dict 来存放 对应年份的公告信息表是否存在 如:{"ReportList_2016_Tbl":True}
#   4.使用utils.base_tools-> dupClassDefine(), addClassDefine()
#     使用uitls.db_tools->execSQL()
# 返回值:
#     返回处理过的带年份的表名列表, 例如: ['report_reportlist_2015_tbl','report_reportlist_2016_tbl']
def parseReportList( filename ):

    if (  not os.path.exists(filename) or os.path.getsize( filename ) <= 10 ):
        print( '文件不存在或无数据:' + filename )
        return False
    
    fp = open( filename, 'r' )
    content = fp.read()
    fp.close()

    # 0. 先清除 report_reportlisttbl 中的记录. 然后遍历公告信息的时候将最新的公告信息
    #    记录添加进该表以及对应年份的公告信息表
    # 0.1  修正, 这儿不能清空report_reportlisttbl, 因为这儿只是处理一个板块的公告信息
    #    应该在外部进行清空处理, 也就是更新所有数据的时候再进行清空处理, 否则会清空其他板块的公告信息
    #sqlstr = 'delete from report_reportlisttbl'
    #execSQL( sqlstr )

    procTblList = []      # 每年的公告存放一张表, 有可能有多年的表

    #print(content)
    
    # 下面的dict是为了映射 每条公告信息的项目对应关系
    d1 = {"0":"stockcode","1":"url","2":"name","3":"type","4":"flag","5":"date","6":"time"}
    d2 = {"ReportListTbl":True}
    # ReportListTbl 实际上是公告列表表的模板, 并不存放数据
    # "ReportList_2016_Tbl":ReportList_2016_tbl 这个对应的事对象

    reg = re.compile(r'(\[\".+?\"\][,|\]])')   # 单条公告数据的正则表达式
    l = re.findall( reg, content )             # 返回结果是各List, 以下同

    print(" 公告数量%d" % len(l) )
    for item in l:   #  逐条处理公告信息
        #print("-----")
        #print(item)
        
        reg2 = re.compile(r'(\".+?\"[,|\]])')
        l2 = re.findall( reg2, item)            # 解析单条公告数据
        i = 0
        rec = {}                                # 存放公告信息的dict
        for item2 in l2:
            #print("====")
            ll = len(item2)
            #print(d1["%d" % i]+":"+item2[1:ll-2])
            rec[d1["%d" % i]] = item2[1:ll-2]    # 利用之前的字典d 的值作为rec 的key
            i += 1

        #print(rec)
        # 1.1 下面是用数据对象来对数据持久化, 创建对应年份的公告信息表
        reportTblName = "ReportList_"+rec["date"][:4]+"_Tbl"
        #print("reportTblName="+ reportTblName)
        if ( reportTblName not in d2 or not d2[reportTblName] ):    # 如果该公告年份对应的表及数据对象不存在
            '''
            # 2016-11-20 :
            #     不在修改models.py， 不添加对应年份的公告信息表, 该表的操作都是直接数据库操作.
            #     因为如果修改了, makemigrations/migrate 会提示表已经存在, 结果操作失败.
            # 创建数据对象及对应的数据库表,并修改d2 中的标识
            #print("parseReportList():自身目录:"+os.path.dirname(__file__))
            #print("parseReportList():目录:"+os.getcwd())
            src = os.path.dirname(__file__)+"/models.py"
            clsdefine = dupClassDefine( src,"ReportListTbl", reportTblName, "utf-8")
            addClassDefine( src, reportTblName, clsdefine, "utf-8" )
            '''
            sqlstr = "create table IF NOT EXISTS report_" + reportTblName + " like report_reportlisttbl"
            logger.log(30,"+++++++++============================")
            logger.log(20,"sqlstr=" + sqlstr)
            execSQL( sqlstr )
            # 下面是数据对象动态实例化, 然后存数据
            #di = __import__('report.reportlist.models',
            #                globals(),locals,["ReportListTbl",reportTblName])
            #c = getattr( di, reportTblName )
            #d2[reportTblName] = c()
            #print(d2[reportTblName])
            #d2[reportTblName] = getattr( di, reportTblName )
            d2[reportTblName] = True    # 上面的动态更新py 文件第一次运行会出现对象找不到

        # 1.1 保存数据到report_reportlisttbl 和对应年份的公告信息表
        #   report_reportlisttbl 只保留最新的公告信息
        #   对应年份的公告信息表保留所有的公告信息, 检索历史信息的时候才使用该表
        # 1.1.1 保存公告到report_reportlisttbl
        sqlstr = "insert IGNORE into report_reportlisttbl" \
                " (`stockcode`,`reporturl`,`reportname`,`reporttype`,"\
                "`flag1`,`releaseddate`,`releasedtime`) values ('" + \
                rec["stockcode"] + "','"+rec["url"]+"','" + rec["name"]+ \
                "','" + rec["type"]+"','" + rec["flag"]+"','"+rec["date"]+ \
                "','" + rec["time"] + "' )"
        #print(sqlstr)
        execSQL( sqlstr )

        # 1.1.2  保存公告到类似report_reportlist_2016_tbl 的对应年份的公告信息表中
        sqlstr = "insert IGNORE into report_"+ reportTblName + \
                " (`stockcode`,`reporturl`,`reportname`,`reporttype`,"\
                "`flag1`,`releaseddate`,`releasedtime`) values ('" + \
                rec["stockcode"] + "','"+rec["url"]+"','" + rec["name"]+ \
                "','" + rec["type"]+"','" + rec["flag"]+"','"+rec["date"]+ \
                "','" + rec["time"] + "' )"
        #print(sqlstr)
        execSQL( sqlstr )

        if ( ('report_' + reportTblName) not in procTblList ):
            procTblList.append( 'report_'+ reportTblName )
        '''
        # 用model 对象进行数据持久化的时候, 无法解决数据重复造成插入失败异常的问题
        p1 = d2[reportTblName](stockcode =rec["stockcode"],
                                      reporturl = rec["url"],
                                      reportname = rec["name"],
                                      reporttype = rec["type"],
                                      flag1 = rec["flag"],
                                      releaseddate = rec["date"],
                                      releasedtime = rec["time"]
                                      )
        p1.save()
        '''

    return procTblList

class testa():
    name = "test"

    def showname(name):
        name = "Adams"
        print(name)

'''
filename = 'G:/0.Data/Report Data/20161031/sme20161031_1.txt'
#parseReportList(filename)

d = {"ReportList_2016_tbl":True}
#tname = "ReportList_2016_tbl"
tname="hello"

if ( (tname not in d ) or not d[tname]):
    print("d中没有"+tname)
else:
    print(d[tname])
    

m = __import__('parseReportList', globals(), locals(), ['testa']) 
c = getattr(m, 'testa') 
myobject = c()

myobject.showname()
'''
