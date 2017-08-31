# -*- coding: utf-8 -*-
import time
import datetime

# 1. isValidDateStr()
#    检查目标日期字符串是否是合法的日期时间
def isValidDateStr( datestr ):
    try:
        dateArray = time.strptime( datestr, "%Y-%m-%d")
    except:
        return False
    return True
        
a = "2012-3-233"
if isValidDateStr( a ):
    print(a+" is valid date")
else:
    print(a + " isn't valid date")

# 2. countDays()
#    计算日期之间的天数(不包括起始日期当天, 比如1号与3号间隔2天)
#  start        起始日期
#  end          结束日期
#  返回值:
#       -1      日期格式非法
#  依赖:
#      isValidDateStr()    本模块方法
#      import datetime
#      python 3.4.2
def countDays( start, end ):
    if ( not isValidDateStr(start) or not isValidDateStr(end) or end < start ) :
        return -1
    
    d1 = datetime.datetime.strptime( start, "%Y-%m-%d")
    d2 = datetime.datetime.strptime( end, "%Y-%m-%d")
    
    return ((d2-d1).days )
    

start = "2016-10-12"
end = "2016-10-24"
print("start="+start+",end="+end )
print( countDays(start, end ))
