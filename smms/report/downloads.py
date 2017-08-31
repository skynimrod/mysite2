# -*- coding: utf-8 -*-

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
    
# 下载函数
def Downloads( url, des, filename ):

    # 1. 如果目标存放目录不存在则创建
    if not os.path.exists( des ):    
        os.makedirs( des )

    f = urllib.request.urlretrieve( url,
                des +'/'+ filename, reporthook = urlcallback )

    #print(f.filename)
    #print(f.headers)
    print(type(f))
    print(f)
    print(f[0])
    print(f[1])

    # 返回值 f 存放的是包含两个元素(filename, headers)的元组 tuple
    # filename 表示保存到本地的路径, header 表示服务器的相应头
    # >>> print(f)
    # ('f:/f_3_test/3_Python/text.txt',
    #  <http.client.HTTPMessage object at 0x0000000002FABE48>)
