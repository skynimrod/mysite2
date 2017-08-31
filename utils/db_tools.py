# -*- coding: utf-8  -*-

# 参见:
#   http://www.cnblogs.com/BeginMan/archive/2013/05/27/3101322.html

#
def execSQL( sqlstr ):
    from django.db import connection, transaction

    cursor = connection.cursor()        # 获得一个游标(cursor)对象

    # 更新操作
    cursor.execute( sqlstr )    # 执行 sql 语句
    #transaction.commit_unless_managed()    # 提交到数据库


def querySQL( sqlstr ):
    from django.db import connection, transaction

    cursor = connection.cursor()        # 获得一个游标(cursor)对象

    # 更新操作
    cursor.execute( sqlstr )    # 执行 sql 语句
    #transaction.commit_unless_managed()    # 提交到数据库

    raw = cursor.fetchall()  # 返回的事tuple类
    #print(raw)
    #print(type(raw))

    return raw
