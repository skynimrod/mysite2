# -*-  coding: utf-8  -*-

import re

# 1. 获取字符串前段的空格数

def getLspaceCount( str ):
    count = 0
    for c in str:
        if c.isspace():
            count ++
        else:
            break
    return count

# 2. 
# 用汉字来拆分字符串, 主要是处理拼音汉字混排的情况, 返回列表
# 比如"岸àn版bàn" , 处理后的结果为:['岸', 'àn', '版', 'bàn']
def splitByHZ( src ):
    reg = re.compile(r'[\u4e00-\u9fa5]')   # 单条公告数据的正则表达式
    li = []
    buf = ''
    for c in src:
        l = re.findall( reg, c )             # 返回结果是各List, 以下同
        if ( len(l)>0 ):   # 中文
            if ( len(buf)>0 ):  # 将之前的字符串加入列表
                li.append(buf)
                buf = ''    # 添加后之前的拼音清零
            li.append(c)
        else:
            buf += c

    if ( len(buf)>0):    # 最后的一部分，不能拉下
        li.append(buf)

    return li
