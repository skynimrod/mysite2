# -*- coding: utf-8 -*-

# 主要是一些涉及URL 相关的功能的封装

# 1. isValidURL()      判断是否是有效的URL
# 2. Downloads()       下载目标URL的内容

# 1. isValidURL()      判断是否是有效的URL
#    参数:
#         url        带检测的url
#    返回值
#         Ture/False
#    依赖:
#         urllib       Python 3.4.2 +
#                      urllib.request代替urllib2
from urllib.request import urlopen
from urllib.error import URLError

# 下面的库是多线程断点续传用的库. 比用urllib 要先进一些
import threading,sys
import requests
import time
import os

    
def isValidURL( url ):
    ret = False
    try:
        response = urlopen( url )
    except URLError as e:
        if hasattr( e, 'reason'):  # stands for URLError
            print("cannot reach a server. ")
        elif hasattr( e, 'code' ) : # stands for HTTPError
            print('find http error.')
        else: # stands for unknown error
            print('unknown error.')
    else:
        print('url is reachable!')
        response.close()
        ret = True
    finally:
        pass
    return ret

'''
url = 'http://www.cninfo.com.cn/disclosure/fulltext/plate/shmblatest_24h.js'
if isValidURL(url):
    print('合法的url:' + url )
else:
    print('不可用的url:'+url)
'''

import os
import urllib.request

# 下载回调函数, 用于显示下载进度
def urlcallback( a, b, c):
    '''
    call back function
    a    downloaded data size
    b    data size
    c    remote file size
    '''
    
    prec = 100.0 * a * b / c
    if 100 < prec:
        prec = 100

    print( "...............%.2f%%\n" % prec, end = '' )

# 0.1 获取ETag, 从而判断是否需要重新下载
def getETAG( url ):
    ETag = requests.head( url ).headers['ETag']
    return ETag
    
# 2. 下载函数
def Downloads( url, des, filename ):

    # 1. 如果目标存放目录不存在则创建
    if not os.path.exists( des ):    
        os.makedirs( des )

    f = urllib.request.urlretrieve( url,
                des +'/'+ filename, reporthook = urlcallback )

    #print(f.filename)
    #print(f.headers)
    #print(type(f))
    #print(f)
    print(f[0])   # 下载后保存的文件(带路径), str 类型
    print(f[1])   # 对方服务器发送的响应消息, 包括文件大小.  http.client.HTTPMessage 类型(也是作为str返回的)
    print("---aaasdf-----")
    print(type(f[0]))
    print(type(f[1]))
    # HTTPMessage 实例持有从 HTTP response 返回的头部。是Hash表, 用f[1]["ETag"]格式访问

    '''
    G:/0.Data/Report Data//20170405/cyb20170405_1.txt
    Date: Wed, 05 Apr 2017 01:13:31 GMT
    Server: Apache
    Last-Modified: Tue, 04 Apr 2017 23:54:41 GMT
    ETag: "2062ac1-287b-54c5fffd05240"
    Accept-Ranges: bytes
    Content-Length: 10363
    Connection: close
    Content-Type: text/javascript
    '''
    print( "ETag的值为:" + f[1]["ETag"])
    print( "文件大小为:" + f[1]["Content-Length"])
    print( "Last-Modified为:" + f[1]["Last-Modified"])
    # 提取Last-Modified和Content-Length, 依此来判断下载内容与之前的下载内容是否一样
    return f
    

    # 返回值 f 存放的是包含两个元素(filename, headers)的元组 tuple
    # filename 表示保存到本地的路径, header 表示服务器的相应头
    # >>> print(f)

    #

class DownloadThread(threading.Thread):
    def __init__(self,url,startpos,endpos,f):
        super(DownloadThread,self).__init__()
        self.url = url
        self.startpos = startpos
        self.endpos = endpos
        self.fd = f
        self.len=0

    def download(self):
        #print("start thread:%s at %s" % (self.getName(), time.time()))
        headers = {"Range":"bytes=%s-%s"%(self.startpos,self.endpos)}
        res = requests.get(self.url,headers=headers)
        # res.text 是将get获取的byte类型数据自动编码，是str类型， res.content是原始的byte类型数据
        # 所以下面是直接write(res.content)
        self.fd.seek(self.startpos)
        self.fd.write(res.content)
        self.len = len(res.content)
        #print("stop thread:%s at %s" % (self.getName(), time.time()))
        # f.close()

    def run(self):
        self.download()

'''
/*
 * 2. MulThreadDownload()
 *        多线程下载.
 *    入口参数:
 *        url           需要下载的URL
 *        desfile       下载后的文件存放名称(含路径, 如果没有路径存放在当前路径下)
 *        threadnum     线程数量, 最大为5， 缺省为3
 *    出口参数:
 *        无
 *    返回值:
 *        "" 表示下载失败. 成功的话就会返回 ETag 的值. 下回就可以比较ETag 来判断是否文件发生变化, 是否需要进一步处理.
 */
'''
def MultThreadDownload( url, path, filename, threadnum = 3 ):
    ret = ""
    filesize = int(requests.head(url).headers['Content-Length'])
    print("%s filesize:%s"%("要下载的文件大小为:",filesize))

    ETag = requests.head(url).headers['ETag']
    print("ETag:%s"%(ETag))
    #线程数最大不能超过5个, 缺省为3个
    if ( threadnum > 5 ):
        return ret
    
    #信号量，同时只允许指定个数的线程运行
    threading.BoundedSemaphore(threadnum)
    # 默认3线程现在，也可以通过传参的方式设置线程数
    step = filesize // threadnum
    mtd_list = []
    start, end = 0, -1

    # 请空并生成文件
    desfile = path + '/' + filename
    tempf = open( desfile,'w')
    tempf.close()
    # rb+ ，二进制打开，可任意位置读写
    l = 0
    with open( desfile,'rb+') as  f:
        fileno = f.fileno()
        # 如果文件大小为11字节，那就是获取文件0-10的位置的数据。如果end = 10，说明数据已经获取完了。
        while end < filesize -1:
            start = end +1
            end = start + step -1
            if end > filesize:
                end = filesize
            # print("start:%s, end:%s"%(start,end))
            # 复制文件句柄
            dup = os.dup(fileno)
            # print(dup)
            # 打开文件
            fd = os.fdopen(dup,'rb+',-1)
            # print(fd)
            t = DownloadThread(url,start,end,fd)
            t.start()
            l += t.len
            mtd_list.append(t)

        for i in  mtd_list:
            i.join()    #  http://blog.csdn.net/zhiyuan_2007/article/details/48807761
                        #
    print("filesize=%d,l = %d" % (filesize, l))
    return ETag

import datetime

dt = datetime.datetime.now()
pathsuffix = dt.strftime('%Y')+"/"+dt.strftime('%m')
print(pathsuffix)
