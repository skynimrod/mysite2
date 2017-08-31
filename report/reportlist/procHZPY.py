# -*- coding: utf-8  -*-

import re

# 构建 汉字拼音 初始化数据 JSON

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

# 这个是转换成 首字母与英文字母对应的, 主要是过滤 a o e, 有些 单元音汉字的首字母需要转换为英文字母
def splitByHZ2( src ):
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
        else:  # 下面将元音改为英文字母, i u ü 没有首字母的汉字, 不处理, 这儿的处理也会把辅音中的a o e 改了, 不过不影响使用
            if ( c in [ "ā", "á", "ǎ", "à"] ):
                c = "a"
            elif ( c == "ō" or c == "ó" or c == "ǒ" or c == "ò" ):
                c = "e"
            elif ( c == "ē" or c == "é" or c == "ě" or c == "è" ):
                c = "e"
            buf += c

    if ( len(buf)>0):    # 最后的一部分，不能拉下
        li.append(buf)

    return li




# 预处理一下hzpy.txt, 保证拼音和汉字都各占单独一行.
def preProc( src, des):
    fs = open(src, 'r')
    fd = open( des, 'w')

    buf = ''
    while(True):
        tmpbuf = fs.readline().strip('\n')
        if ( not tmpbuf ):
            print("预处理结束！")
            break
        if ( len(tmpbuf) == 0 ):     # 空行
            continue
        
        reg = re.compile(r'[\u4e00-\u9fa5]')   # 单条公告数据的正则表达式
        l = re.findall( reg, tmpbuf )             # 返回结果是各List, 以下同
        if ( len(l) > 0 and len(tmpbuf) >0 ):  # 表示是汉字与拼音混排了
            li = splitByHZ( tmpbuf )
            for c in li:
                buf += c + '\n'
        else:
            buf += tmpbuf + '\n'

    fd.write(buf)
    fd.close()
    fs.close()

preProc("hzpy.txt", "p_hzpy.txt")

# 这个是处理2501个汉字的模块 
def buildHZPYJson():
    src = "hzpy.txt" 
    des = "hzpyJson.txt"

    preProc("hzpy.txt", "p_hzpy.txt")
    src = "p_hzpy.txt"

    modelstr = '"model":"report.hzpyTbl",'

    fs = open( src, 'r')
    fd = open( des, 'w+' )

    py = hz = ''
    jsonstr = '[ \n'
    while(True):
        py = fs.readline().strip('\n')
        if ( not py ):
            print("处理结束！")
            break
        hz = fs.readline().strip('\n')
        if ( not hz ):
            print("处理结束！")
            break
        if ( len(py) == 0 or len(hz) == 0):  # 只要有一个是空行就跳过
            continue
        jsonstr += '    {' + modelstr + '"fields":{"py":"'+py+'","hz":"'+hz+'"}},\n'
            
            

    jsonstr += ']'

    fd.write(jsonstr)
    
    fd.close()
    fs.close()


#buildHZPYJson()

# 将拼音字符串中的aoe 转换为英文字母aoe
def aoeFilter( src ):
    buf = ''
    for c in src:
        # 下面将元音改为英文字母, i u ü 没有首字母的汉字, 不处理, 这儿的处理也会把辅音中的a o e 改了, 不过不影响使用
        if ( c in [ "ā", "á", "ǎ", "à"] ):
            c = "a"
        elif ( c == "ō" or c == "ó" or c == "ǒ" or c == "ò" ):
            c = "e"
        elif ( c == "ē" or c == "é" or c == "ě" or c == "è" ):
            c = "e"
        buf += c

    return buf
            

# 这个是处理6981个汉字的模块 
def buildHZPY2Json( src, des ):

    modelstr = '"model":"report.hzpyTbl",'

    fs = open( src, 'r')
    fd = open( des, 'w+' )

    py = hz = ''
    jsonstr = '[ \n'
    while(True):
        py = fs.readline().strip('\n')
        if ( not py ):
            print("处理结束！")
            break
        py = aoeFilter( py )      # 过滤掉拼音aoe, 替换成对应的英文字母aoe
        py_list = py.split(" ")    # 拼音列表

        hz = fs.readline().strip('\n')
        if ( not hz ):
            print("处理结束！")
            break
        
        if ( len(py) == 0 or len(hz) == 0):  # 只要有一个是空行就跳过, 容错处理而已
            continue
        hz = hz.replace('','')        # 原始数据文档中的汉字行有时候有非法字符, 过滤
        i = 0
        for pystr in py_list:
            jsonstr += '    {' + modelstr + '"fields":{"py":"'+pystr+'","hz":"'+hz[i]+'"}},\n'
            i += 1

    jsonstr += ']'

    fd.write(jsonstr)
    
    fd.close()
    fs.close()



c = "ā"
print(c)
if ( c in [ "ā", "á", "ǎ", "à"] ):
    c = "a"
print(c)
buf = "àn àn ān ǎn ān ān àn áng àng āng ào āo áo ào ào ǎo ào áo"
l = buf.split(" ")
print(l)

print( aoeFilter(buf))



buf = "吖啊嗄腌锕阿哀哎唉嗌嗳埃嫒挨捱暧爱瑷癌皑"
print(buf[0])
print(type(buf[0]))

buf ="傥唐堂塘帑惝搪棠樘汤淌"
buf = "粽纵综腙踪鬃奏揍诹走邹鄹陬"
print(buf)
buf = buf.replace('','')
print(buf)

src = "hzpy2.txt" 
des = "hzpyJson2.txt"

buildHZPY2Json( src, des )
    
src = "缺录的汉字列表.txt" 
des = "hzpy_init_2.json"

buildHZPY2Json( src, des )
