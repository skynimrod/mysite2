# -*- coding: utf-8   -*-

from django.shortcuts import render

from django.http import HttpResponseRedirect, HttpResponse


from django.urls import reverse
from django.views import generic

from datetime import date
import datetime
from datetime import timedelta

from report.conf import report_setting
from report.reportlist.models import ReportDownLoadsInfoTbl, ReportListTbl
from report.reportlist.downloadReportList import getReportList

from report.reportlist.parseReportList import parseReportList

from utils.url_tools import Downloads

from utils.db_tools import execSQL,querySQL
# Create your views here.

import logging

logger = logging.getLogger(__name__)
adamslogger = logging.getLogger('adamslogger' )

# 公告列表处理首页
# 这个页面显示的是公告列表相关处理的功能连接
#  1. 更新公告数据
#  2. 处理公告数据
#  3. 检索公告数据
def index( request ):
    print(logger)
    print(adamslogger)
    logger.error('测试错误日志')
    logger.debug('测试debug日志')
    logger.warning('测试warning日志')
    logger.info('测试info日志')
    logger.critical('测试critical日志')
    adamslogger.debug('日志for adamslogger->debug')
    return render( request, 'report/index.html')
    #return HttpResponseRedirect( reverse( 'report:index' ) )

# 下载公告列表
def DownloadReportListView( request ):
    desDir = report_setting.REPORT_DIR

    template_name = 'report/download.html'
    context_object_name = 'report_list_RawData'

    #reportUrls = ReportDownLoadsInfoTbl.objects.filter()
    reportUrls = ReportDownLoadsInfoTbl.objects.all()
    print( reportUrls )
    for report in reportUrls:
        print( report.url )
    getReportList( reportUrls, desDir )


    '''
    print('-------------------------------------------')
    tt = __import__('report.reportlist.downloadReportList',
                    globals(),locals,['test'])

    test = tt.test

    print(tt)
    test.showname()
    print('===============')
    tt.getReportList(reportUrls, desDir)
    '''
    #return HttpResponseRedirect( reverse( 'report:DownloadResult', args=( question.id,) ) )
    return HttpResponseRedirect( reverse( 'report:index' ) )

# 更新公告列表, 这儿的传入参数是起始日期和结束日期字符串
# http://localhost:8000/report/update?startdate=2016-11-05&enddate=2016-11-05
def updateReportListView( request ):
    reportDir = report_setting.REPORT_DIR   # 公告列表文件存放的路径
    #sqlstr = "create table IF NOT EXISTS report_reportlist_2015_tbl like report_reportlisttbl"
    #execSQL(sqlstr)
    startdate = request.GET.get('start')
    enddate = request.GET.get('end')
    
    
    if ( not startdate ):
        d1 = date.today()
        print(d1)
    else:
        d1 = datetime.datetime.strptime( startdate, "%Y-%m-%d")
    if ( not enddate ):
        d2 = date.today()
        print(d2)
    else:
        d2 = datetime.datetime.strptime( enddate, "%Y-%m-%d")

    # 0. 清空 最新公告的信息内容 report_reportlisttbl
    sqlstr = 'delete from report_reportlisttbl'
    execSQL( sqlstr )


    days = (d2-d1).days      # 
    i = 0
    d = d1
    reportset = ['shmb', 'szse', 'sme', 'cyb' ]
    while( i <= days ):
        datestr = d.strftime( '%Y%m%d' )
        pathstr = reportDir + '/' + datestr
        
        for item in reportset :
            filename = pathstr + '/' + item +datestr+'_1.txt'   
            li = parseReportList( filename )

            filename = pathstr + '/' + item +datestr+'_2.txt'   
            li = parseReportList( filename )

            # 仅处理最新的公告
            buildStockBriefInfoTbl( 'report_reportlisttbl' )  
                
        i+= 1
        d = d1 + timedelta(days=i)
    return HttpResponseRedirect( reverse( 'report:index' ) )

# 检索公告信息，
#  这儿仅仅是检索界面, 根据检索条件检索出结果.
# 传入信息:
#    登录信息(如果登录就是游客guest)
#    检索条件是:
#        1. 自选股
# 页面设计思路:
#    1. 缺省, 没有检索条件的时候, 显示最新的公告信息, 也就是report_reportlisttbl中的信息
#    2. 由于修改了数据访问方式, 使用RawSQL访问, 而不是models 方式, 那么返回的不再是querySet,
#       而是 tuple.  那么 对应的页面模板的处理也要修改. 
def showAllView( request ):
    # 1. 根据用户登录信息获取对应的功能菜单
    #menu = getMenu( userid )    
    # 2. 返回检索结果
            #di = __import__('report.reportlist.models',
            #                globals(),locals,["ReportListTbl",reportTblName])
            #c = getattr( di, reportTblName )
            #d2[reportTblName] = c()
            #print(d2[reportTblName])
            #d2[reportTblName] = getattr( di, reportTblName )
            #d2[reportTblName] = True    # 上面的动态更新py 文件第一次运行会出现对象找不到
    '''
    # 放弃通过models 访问带年份的公告信息表的模式, 因为该类如果动态添加后, 初始化的时候有些错误
    # 或者可以通过类似django 的makemigrations的机制, 处理数据前必须先预处理
    #  (也就是获取可能的带年份的公告表类,
    #    然后后台运行manage.py  makemigrations report/manage,py migrate 来更新model对象和数据库表)
    #  这种预处理的方式, 需要测试是否能动态的执行.
    # 暂时放弃, 直接用raw SQL 的操作方式.
    
    reportTblName = 'ReportList_2016_Tbl'
    r1 = __import__('report.reportlist.models', globals(), locals(),
                    ['ReportListTbl', reportTblName ])
    c = getattr( r1, reportTblName )
    
    reportset1 = c.objects.filter( releaseddate__gte ='2016-11-09',
                                   stockcode__icontains ='603').order_by(
                                       "stockcode","-releasedtime")  # 带-表示降序
    

    reportset = reportset1
    
    sqlstr = 'select * from report_reportlisttbl ' + \
                ' order by stockcode asc, releasedtime desc ' + \
                ' limit 20 '
    reportset = querySQL( sqlstr )
    print(sqlstr)
    '''
    reportset = ReportListTbl.objects.all().order_by(
                        "-releasedtime","stockcode")  # 带-表示降序
    prefix = "http://www.cninfo.com.cn/"

    return render( request, 'report/showall.html',
                   {"reportset":reportset,
                    "prefix":prefix,
                    "pagenum":20,} )

def showSelectedView( request ):
    '''
    reportset1 = ReportList_2016_tbl.objects.get( releaseddate='2016-11-10')
    reportset2 = ReportList_2016_tbl.objects.get( releaseddate='2016-11-09')

    reportset = reportset1 | reportset2
    
    '''
    print("in showSelectedView ")
    buf = "teeee"
    print(buf)
    return HttpResponse(buf)
    #return render( request, 'report/showall.html' )

# 调试功能 tmp
#     clearView()  清除一些数据或表, 便于进行测试
def clearView(request):
    # 1. 清除 Report_reportlist_2015_tbl
    sqlstr = "drop table IF EXISTS report_reportlist_2015_tbl"
    execSQL(sqlstr)
    # 2. 清除 Report_reportList_2016_tbl
    sqlstr = "drop table IF EXISTS report_reportlist_2016_tbl"
    execSQL(sqlstr)

    return HttpResponseRedirect( reverse( 'report:index' ) )


# 微信开发接口测试
import hashlib
def mptestView( request ):
    
    signature   = request.GET.get('signature')
    timestamp   = request.GET.get('timestamp')
    nonce       = request.GET.get('nonce')
    echostr     = request.GET.get('echostr ')

    if ( not signature):
        signature = "signature"

    if ( not timestamp):
        timestamp = "timestamp"

    if ( not nonce):
        nonce = "nonce"

    if ( not echostr):
        echostr = "echostr"

    token = "rMoonSta1234oHello1234"
    print(" signature=%s, \r\n timestamp=%s, nonce=%s, echostr=%s" % (signature, timestamp, nonce, echostr ) )

    a1 = [ token, timestamp, nonce ]
    print(a1)

    a2 = sorted(a1)
    print(a2)

    tmp = ''.join(a2)
    print(tmp)
    buf = tmp.encode("utf-8")
    print(buf)

    sha = hashlib.sha1(buf) #或hashlib.md5()

    encrypts = sha.hexdigest() #生成40位(sha1)或32位(md5)的十六进制字符串
    print( encrypts )

    if ( encrypts == signature ):
        print("校验通过")
        return HttpResponse(echostr)
    else:
        print("校验失败!")
        return HttpResponse("False")
    
       
#------------------------------

# Ajax 测试
# select a.reporturl, a.reportname from report_reportlist_2016_tbl a, report_reportfiltertbl b
#            where LOCATE(b.key, a.reportname)>1;
# select count(*) from report_reportlist_2016_tbl a, report_reportfiltertbl b
#            where LOCATE(b.key, a.reportname)>1;
def ajaxtest(request ):
    print("in ajaxtest==============")
    #print( request.GET.items())
    #print( request.POST.items())
    p1 = request.POST.get('pagenum')
    #p1 = pagenum
    csrftoken = request.POST.get('csrfmiddlewaretoken')

    start = request.POST.get('start')
    end = request.POST.get('end')

    if not p1 :
        p1 = 18
        print('没有获取到pagenum参数')
    else:
        print("pagenum="+p1)

    if not csrftoken:
        print('没有获取到csrftoken参数')
    else:
        print("csrftoken="+csrftoken)

    if not start :
        print('没有获取到start参数')
        start = '0'
    else:
        print("start="+start)

    if not end :
        print('没有获取到end参数')
        end = pagenum
    else:
        print("end="+end)

    # 测试 查询结果
    subclause = 'where '
    sqlstr = "select `key` from report_reportfiltertbl "    # 现在的flag 初始化是不过滤得, 应该初始化为过滤..
    qs = querySQL(sqlstr)
    print( "关键字总数 %d" % len(qs))

    

    sqlstr = "select count(*) from report_reportlist_2016_tbl a where not exists (select * from report_reportfiltertbl b where LOCATE(b.key, a.reportname)>1);"    

    #sqlstr = "select * from report_reportlisttbl order by releasedtime desc, stockcode asc  "
    #sqlstr += " limit "+ start + "," + end

    # 先返回所有的最新公告数量
    sqlstr = "select count(*)  from report_reportlisttbl"
    qs = querySQL( sqlstr )
    total = qs[0][0]
    print( "最新公告总共有: %d" % total )

    sqlstr = "select count(*) from report_reportlisttbl a where not exists " + \
               " (select * from report_reportfiltertbl b where LOCATE(b.key, a.reportname)>1)" 
    qs = querySQL(sqlstr)
    validtotal = qs[0][0]
    print( "最新有效公告总共有: %d" % validtotal )

    sqlstr = "select * from report_reportlisttbl a where not exists " + \
               " (select * from report_reportfiltertbl b where LOCATE(b.key, a.reportname)>1)" + \
               " order by releasedtime desc, stockcode asc  "
    sqlstr += " limit "+ start + "," + end
    print(sqlstr)
    raw = querySQL(sqlstr)
    print('===select * 查询结果类型====================')
    print(type(raw))

    buf = '<ul><li>最新公告数量: %d ( %d ) </li>' % ( validtotal, total )
    
    prefix = "http://www.cninfo.com.cn/"
    i = int(start) +1
    pre_stockcode = ''
    pre_date = ''
    flag = False            # flag = False 标识是第一次处理
    for report in raw:
        print(report)
        stockcode = report[1]
        stockname = report[3].split("：")[0]
        url = prefix + report[2]
        reportname = report[3]
        rdate = report[6]
        if ( stockcode != pre_stockcode or pre_date != rdate ):
            print(pre_stockcode+"|"+stockcode)
            pre_stockcode = stockcode
            print(pre_date+"|"+rdate)
            pre_date = rdate
            if ( flag  ):           # 除了第一次, 后面每次处理为前一次的<ul> 添加匹配的</ul>, 最后一个进不了循环内, 在外围加</ul>
                buf += '</ul>'
            else:
                flag = True         # 第一次处理的时候不加</ul>，因为还没开始处理.  变更flag 为True 标识开始处理了， 这儿只执行一次
            buf += '<li>'+stockcode + ' ( '+stockname+ ':' + name2py(stockname) +' )---(' + rdate+') </li><ul>'

        buf +='<li><a href="'+url+'" target="_blank">%d ' % i + '. ' + stockcode +'   '+reportname+'----'+rdate+' </a></li>'
        # 格式为: stockcode(name):reportname -- releaseddate
        #buf += '<li><a href="'+prefix+report[2]+'"'+'>'+item[1]
        #        '('+report[3][:4]+')  '+ \
        #        report[3]+'----'+report[6]+' </a></li>'
        i += 1
    buf += '</ul></ul>'   # 第一个</ul> 是最后一次处理的</ul>  第二个</ul> 是外围</ul>
    '''
    (234, '603633', 'finalpage/2016-11-08/1202818988.PDF', '徕木股份：首次公开发行A
    股网上申购情况及中签率公告', 'PDF', '448', '2016-11-08', '2016-11-08 00:00')
    '''
    #buf = "<p>页面数据为:" + p1+",csrftoken="+csrftoken +"</p>"
    #buf = "==="
    print(buf)
    return HttpResponse(buf)

# Ajax: 返回 自选股查询结果
def selfselected( request ):
    print("in selfselected==============")
    #print( request.GET.items())
    #print( request.POST.items())
    p1 = request.POST.get('pagenum')
    #p1 = pagenum
    csrftoken = request.POST.get('csrfmiddlewaretoken')

    start = request.POST.get('start')
    end = request.POST.get('end')

    if not p1 :
        p1 = 18
        print('没有获取到pagenum参数')
    else:
        print("pagenum="+p1)

    if not csrftoken:
        print('没有获取到csrftoken参数')
    else:
        print("csrftoken="+csrftoken)

    if not start :
        print('没有获取到start参数')
        start = '0'
    else:
        print("start="+start)

    if not end :
        print('没有获取到end参数')
        end = pagenum
    else:
        print("end="+end)

    # 测试 查询结果
    buf = '<ul>'

    if ( start == '0' ):  # 只有第一个查询结果才会显示公告数量
        # 先返回所有的最新公告数量
        print("---------第一页 需要计算数量-------------")
        sqlstr = "select count(*)  from report_reportlisttbl"
        qs = querySQL( sqlstr )
        total = qs[0][0]
        print( "最新公告总共有: %d" % total )

        sqlstr = "select count(*) from report_reportlisttbl a where not exists " + \
                   " (select * from report_reportfiltertbl b where LOCATE(b.key, a.reportname)>1)" 
        qs = querySQL(sqlstr)
        validtotal = qs[0][0]
        print( "最新有效公告总共有: %d" % validtotal )

        sqlstr = "select count(*) from report_reportlisttbl a where exists " + \
                   " (select * from report_selfselectedtbl b where b.stockcode=a.stockcode)" 
        qs = querySQL(sqlstr)
        selftotal = qs[0][0]
        print( "最新自选股公告总共有: %d" % selftotal )

        buf +='<li>最新公告数量: %d [%d ( %d )] </li>' % ( selftotal, validtotal, total )

    sqlstr = "select * from report_reportlisttbl a where exists " + \
               " (select * from report_selfselectedtbl b where b.stockcode=a.stockcode)" +\
               " order by releasedtime desc, stockcode asc  "
    sqlstr += " limit "+ start + "," + end
    print(sqlstr)
    raw = querySQL(sqlstr)
    print('===select * 查询结果类型====================')
    #print(type(raw))
    
    prefix = "http://www.cninfo.com.cn/"
    i = int(start) +1
    pre_stockcode = ''
    pre_date = ''
    flag = False            # flag = False 标识是第一次处理
    for report in raw:
        print(report)
        stockcode = report[1]
        stockname = report[3].split("：")[0]
        url = prefix + report[2]
        reportname = report[3]
        rdate = report[6]
        if ( stockcode != pre_stockcode or pre_date != rdate ):
            print(pre_stockcode+"|"+stockcode)
            pre_stockcode = stockcode
            print(pre_date+"|"+rdate)
            pre_date = rdate
            if ( flag  ):           # 除了第一次, 后面每次处理为前一次的<ul> 添加匹配的</ul>, 最后一个进不了循环内, 在外围加</ul>
                buf += '</ul>'
            else:
                flag = True         # 第一次处理的时候不加</ul>，因为还没开始处理.  变更flag 为True 标识开始处理了， 这儿只执行一次
            buf += '<li>'+stockcode + ' ( '+stockname+ ':' + name2py(stockname) +' )---(' + rdate+') </li><ul>'

        buf +='<li><a href="'+url+'"  target="_blank">%d ' % i + '. ' + stockcode +'   '+reportname+'----'+rdate+' </a></li>'
        # 格式为: stockcode(name):reportname -- releaseddate
        #buf += '<li><a href="'+prefix+report[2]+'"'+'>'+item[1]
        #        '('+report[3][:4]+')  '+ \
        #        report[3]+'----'+report[6]+' </a></li>'
        i += 1
    buf += '</ul></ul>'   # 第一个</ul> 是最后一次处理的</ul>  第二个</ul> 是外围</ul>
    '''
    (234, '603633', 'finalpage/2016-11-08/1202818988.PDF', '徕木股份：首次公开发行A
    股网上申购情况及中签率公告', 'PDF', '448', '2016-11-08', '2016-11-08 00:00')
    '''
    #buf = "<p>页面数据为:" + p1+",csrftoken="+csrftoken +"</p>"
    #buf = "==="
    #print(buf)
    return HttpResponse(buf)


# 股票名称转换为拼音简写
def name2py( name ):
    pbuf = ''
    buf = name.replace(' ', '')
    splist = {'Ｂ':'b','Ａ':'a'}
    alphalist = '*ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    for c in buf:
        #  Ｂ->B, Ａ->A, 单独处理, *, S, T 这些都有可能在名字中
        if ( c in ['Ｂ','Ａ'] ):   
            pbuf += splist[c]
            continue
        # 如果本身就是字母, 也不进行转换
        if ( c in alphalist ):
            pbuf += c
            continue
        tmp = hz2py(c)
        if ( len(tmp) > 0 ):    # 没有对应的拼音, 有可能本身就是拼音啥, 
            pbuf += hz2py(c)
        else:
            pbuf += c
            print( name + " || 有非汉字或没有对应拼音的汉字!")  # 昇兴股份  喆没有拼音 舜喆B, 单独添加该汉字
    return pbuf.upper()

# 汉字转换为拼音首字母
def hz2py( hz ):
    sqlstr = "select py from report_hzpytbl where hz = '" + hz + "' limit 1"
    raw = querySQL(sqlstr)
    py = ''
    for rec in raw:
        py = rec[0]
        break
    if (len(py)>0 ):
        return py[0]
    else:
        print(hz + '没有拼音')
        return ''


# 构建(更新) buildStockBriefInfoTbl  股票简明信息表
# 更新公告数据后顺便更新即可
# 1. 通过group by 方式访问report_reportlist...tbl获取 stockbriefinfotbl 中没有的
# 修改:
#     如果 参数为空, 仅仅访问 report_reportlisttbl 中的最新的公告信息,
#     如果参数不为空, 表示要指定年份的公告信息进行信息更新.
# 参数:
#     reportlisttbl     要处理的公告信息表(由于每年会由一张表, 所以要指定)
def buildStockBriefInfoTbl( reportlisttbl ):
    print("buildStockBaseInfoTbl() begin" + reportlisttbl )
    sqlstr = 'select stockcode,substring_index(reportname,"：",1) as stockname ' + \
             '   from ' + reportlisttbl + ' where stockcode not in ' + \
             ' (select stockcode from report_stockbriefinfotbl ) group by stockcode '
    queryset = querySQL( sqlstr )

    ll = len( queryset )
    print("查询结果总数为: %d " % ll )
    for rec in queryset:
        py = name2py( rec[1] )
        #print("rec[1](reportname)="+rec[1] + ":" + py )
        # 下面的SQL 语句中的IGNORE是为了容错, 如果已经有了, 就不添加新记录了
        sqlstr = 'insert IGNORE into report_stockbriefinfotbl (`stockcode`, `stockname`, `stockpy`) ' +\
                 ' values ("' + rec[0] + '","' + rec[1] + '","' + py +'")'
        execSQL(sqlstr)
