# -*-   coding: utf-8  -*-

import os

# 1. 读取指定py 文件中的类定义
#    getClassDefine( filename )
#from utils.str_tools import getLspaceCount
def getLspaceCount( str ):
    #print('str='+str+':')
    count = 0
    for c in str:
        #print("c=:%c" % c + ":")
        if ( c == ' ' ):   # 空格
            count += 1
        else:
            break

    #print( str + '的空格数:%d' % count)
    return count

# 判断目标py文件中是否包含指定的类定义
def hasClassDefine( filename, clsname, encoding ):
    flag = False
    fp = open( filename, "r+", encoding=encoding )
    try:
        while( True ):
            buf = fp.readline()
            
            if (not buf ):  # 文件结束
                break

            if ( buf.isspace() ):  # 跳过空行
                continue

            if (buf.find("class") != -1 and buf.find(clsname) != -1 ):
                flag = True     # 表示找到了类
                break
    except:
        print("error")
    finally:
        fp.close()
    return flag

# 注意, 这个方法返回的类定义，已经删除了类定义中的空行
# 缺: 类依赖定义要添加, 不用添加, 复制的类定义只能添加到原始类定义的相同py文件中.
def dupClassDefine( filename, oldclsname, newclsname,encoding ):

    retstr = ''
    flag = False          # 用来表示是否找到了目标类
    count = -1            # 用来记录目标类定义的第一行的左边空格数
    #print("dupClassDefine():自身目录:"+os.path.dirname(__file__))
    #print("dupClassDefine():目录:"+os.getcwd())
    print(filename)
    fp = open( filename, "r+", encoding= encoding )

    #print(fp)
    try:
        while( True ):
            buf = fp.readline()
            
            if (not buf ):  # 文件结束
                break

            if ( buf.isspace() ):  # 跳过空行
                continue

            if (buf.find("class") != -1 and buf.find(oldclsname) != -1 ):
                count = getLspaceCount( buf )
                flag = True     # 表示找到了类
                retstr += buf.replace(oldclsname, newclsname)
                continue

            # 判断是否到了类结束(也就是下一个类或方法的定义), 缩紧空格数相同
            count2 = getLspaceCount(buf)
            
            if ( flag and count2 == count ):    # 类定义结束了
                break
            elif( flag ):   # 类定义没有结束
                retstr += buf
            
    #except:
       # print("error")
    finally:
        fp.close()

    print('############')
    print(retstr)
    return retstr


# 2. 向指定py文件 添加类定义， 如果已经有同名类定义, 则添加失败
def addClassDefine( filename, clsname, classbuf, encoding ):
    flag = hasClassDefine( filename, clsname, encoding )
    if ( flag ):             # 如果目标py中已经有该类名的类定义, 则添加失败
        return False

    flag = False     # 这儿重用了flag 是为了判断后续的操作是否成功
    fp = open( filename, "a", encoding=encoding )

    try:
        fp.write( classbuf )
    except:
        flag = False
    finally:
        fp.close()

    return flag

'''
newclsname = "newadtest2"
retstr = dupClassDefine("tests.py", "adtest", newclsname, "utf-8")
print(retstr)
addClassDefine("tests.py",newclsname, retstr, "utf-8")

di = __import__('tests',
                            globals(),locals,[newclsname])
c = getattr( di, newclsname )
nc = c()
nc.showname()
'''
