# -*- coding: utf-8 -*-

import datetime

#from utils.url_tools import Downloads
from utils.url_tools import Downloads,MultThreadDownload

def getReportList( reports, desDir ):

    dt = datetime.datetime.now()
    suffix = dt.strftime('%Y%m%d')+ ("_1" if dt.hour < 17 else "_2")
    path = desDir + "/" + dt.strftime('%Y%m%d')

    print("path="+path)
    
    for report in reports:
        url = report.url
        filename = report.filename
        memo = report.memo
        print(url)
        print(filename)
        print(memo)
        filename += suffix+'.txt'
        ret = Downloads(url, path, filename )
        print("下载后的文件为: %s" % ret[0])
        print( "ETag = %s" % ret[1]["ETag"])
        #ETag = MultThreadDownload(url, path, filename, )
        #print("url:%s, ETag:%s" % (url, ETag ))

class test():
    name = ''

    def showname():
        print('this is my name, just a test!')
