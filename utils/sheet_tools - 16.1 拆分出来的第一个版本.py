# -*-  coding: utf-8 -*-
# 表格处理工具中间件
#    处理的原始数据是带画布方式描述的数据, 解析后还原为页面方式. 如果有表格, 则摘取出表格出来.
#

import traceback
class sheetService():
    def __init__(self, textMap, cellMap, cellIndexMap ):
        self.textMap = textMap.copy()
        self.cellMap = cellMap.copy()
        self.cellIndexMap = cellIndexMap.copy()
        self.sheetMap = {}        # 存放拆分出来的表格
        self.text = self.processTxtForTable( textMap, cellMap, cellIndexMap)

    def getSheets( self ):
        return self.sheetMap

    def getText( self ):
        return self.text

    def rlen(self, buf ):
        return int(( len(buf.encode("utf-8"))-len(buf) )/2 + len(buf) )  
    
    #=============== 下面所有方法是涉及文本格式的, 15.decode() 调用
    # 15.1 processTxtForTable()
    # 完成以下任务:
    #     1. 合并本来是一行的文本
    #     2. 格式化显示表格的信息
    # depends on:
    #       delTxt( )
    #       buildCellIndexMap( )
    #       preProcTxtMap( )
    #       preProcTxtMap4Cell()
    #       reProcColRow()
    #       buildTableMap()
    #       buildPageTxt()
    def processTxtForTable( self, textMap, cellMap, cellIndexMap ):
        try:
            retbuf = ""
            print( sorted( cellMap.items(), key=lambda d:d[0]) ) # 按键值进行排序
            print("=======================================")
            print( sorted( textMap.items(), key=lambda d:d[0]) ) # 按键值进行排序

            # 1. 创建cellIndexMap, 存放 单元格对应的txt信息, {单元格编号:文本编号,} , 这个dict后续处理会使用
            #self.buildCellIndexMap( textMap, cellMap, cellIndexMap )
            # 2016.12.22:  这一部分不需要了, 因为在解析文本后就进行了这部分的处理
            print(cellIndexMap)

            # 2. 处理textMap, 将不再表格中的文本进行处理, 如果是同一行的就进行合并
            self.preProcTxtMap( textMap, cellIndexMap )

            # 3. 预处理 表格中的文本, 将原本一行的多个文本拼接为一个文本, 删除多余的文本. 同时修正cellIndexMap中的文本编号信息
            self.preProcTxtMap4Cell( textMap, cellMap, cellIndexMap )
            
            # 4. 预处理 表格, 根据坐标关系归类到列与行, 相关信息存放在 colMap, colIndexMap, rowMap, rowIndexMap
            colMap, colIndexMap, rowMap, rowIndexMap = {}, {}, {}, {}  # 字典不能作为key, 只能再建立一个colIndexMap来记录每个col对应的cell集合
            self.preProcColRow( cellMap, cellIndexMap, colMap, colIndexMap, rowMap, rowIndexMap )
            
            # 5. 解析文本与cell的关系, 拆分出table 出来, 创建tableMap={1:[cellid_list]}， 同时在cellMap 中添加tableid 属性
            tableMap = {}
            self.buildTableMap( textMap, cellMap, cellIndexMap, tableMap, colIndexMap, rowIndexMap )
            print("--after buildTableMap()---cellIndexMap-----------")
            print(cellIndexMap)
            print(tableMap)

            # 6. 输出文本. 已经处理过同行多文本的拼接, 不再cell中的文本就是单独一行文本
            retbuf = self.buildPageTxt( textMap, cellMap, cellIndexMap, tableMap, colIndexMap, rowIndexMap )
            print(retbuf)
            
            return retbuf

            # 用while 来再显示一次, 这次是中间处理表格, 处理完后, 再继续处理文本, 循环中的文本编号要跳过表格处理的那部分
            # 因为表格处理的时候不是按照文本编号的
        except:
            traceback.print_exc()
            print( "processTxtForTable() Exception Error!" )
            return ""
        

    # 15.2 delTxt()
    #    删除文本字典中的某个文本, 需要修改链关系, cellIndexMap 相应的也删除对应文本编号
    #    
    def delTxt(self, item, textMap, cellIndexMap ):
        if ( not item in textMap.keys() ):
            return
        pre_id  = textMap[item]["pre"]
        next_id = textMap[item]["next"]

        if ( pre_id != -1 ):  # 前面有文本的话
            textMap[pre_id]["next"] = next_id

        if ( next_id != -1 ):  # 后面有文本的话
            textMap[next_id]["pre"] = pre_id

        cellId = textMap[item]['cell']
        if ( cellId in cellIndexMap.keys() ):
            if ( item in cellIndexMap[cellId]["txtlist"] ):
                cellIndexMap[cellId]["txtlist"].remove(item)

        del( textMap[item] )
            
    # 15.3 preProcTxtMap()
    #     预处理textMap, 仅限于不在单元格里面的文本进行处理,  将原本在一行的拼接在一行, 删除多余的文本编号, 修正链表
    #     页眉内的文本也进行拼接处理
    # depends on:
    #       delTxt( item, textMap, cellIndexMap )
    # 2017.01.10:
    #     更改实现方式, 循环按照 oy 坐标从上往下处理
    def preProcTxtMap( self, textMap, cellIndexMap ):
        try:
            for k, v in sorted( textMap.items(), key=lambda d:d[1]['o_xy']['oy'], reverse = True ):
                if ( v['cell'] != -1 ):  # 跳过单元格里面的文本(因为单元格的处理比较复杂, 还有很多中间过程)
                    continue
                    
                ox, oy = v['o_xy']['ox'], v['o_xy']['oy']
                pre_id = v['pre']
                
                if ( pre_id != -1 ):          # 如果前面有文本编号
                    pre_ox, pre_oy = textMap[pre_id]['o_xy']['ox'] , textMap[pre_id]['o_xy']['oy']
                    if ( abs(pre_oy - oy) < 1 ):    # 两个Y坐标小于1视为同一行
                        if ( pre_ox <= ox ):                  # 留小不留大, 小的在前面
                            textMap[pre_id]['txt'] += textMap[k]['txt']
                            textMap[pre_id]['length'] = self.rlen(textMap[pre_id]['txt'])
                            self.delTxt( k, textMap, cellIndexMap )
                        else:
                            textMap[k]['txt'] += textMap[pre_id]['txt']
                            textMap[k]['length'] = self.rlen(textMap[k]['txt'])
                            self.delTxt( pre_id, textMap, cellIndexMap )
        except:
            print("preProcTxtMap() Exception Error!")
            traceback.print_exc()
        


    # 15.4 buildCellIndexMap()
    #       构建表格与文本的映射索引关系, 表格编号: 表格中的文本编号列表
    # 2016.12.22:
    #      这部分处理作废了, 因为在解析文本内容的时候就已经做了这部分工作了. 
    def  buildCellIndexMap( self, textMap, cellMap, cellIndexMap ):
        try:
            for k,v in sorted( cellMap.items(), key=lambda d:d[0]):
                for k1,v1 in sorted( textMap.items(), key=lambda d:d[0]) :
                    if ( v1['cell'] == k ):
                        cellIndexMap[k].append(k1)
        except:
            traceback.print_exc()
            print( "buildCellIndexMap() Exception Error!" )
            
    # 15.5 preProcTxtMap4Cell( )
    #      处理单元格中的文字, 对于原来是一行, 但是分为多个文本的拼接为一个文本, 删除textMap中多余的文本子项.
    #      同时更新cellIndexMap 中对应的文本编号列表信息, 删除对应的文本编号
    #      同时修正 cellMap 中的最大文本长度 maxlen
    # depends on:
    #       delTxt()
    def preProcTxtMap4Cell( self, textMap, cellMap, cellIndexMap ):
        try:
            for k,v in sorted( cellMap.items(), key=lambda d:d[0]):
                if (len( cellIndexMap[k]["txtlist"] ) <= 1 ):  # cell 中多余1个文本的才进行处理, 单个文本不存在是否需要拼接的问题
                    continue
                
                txtlist = cellIndexMap[k]["txtlist"].copy()    
                preTxt = {}      # 中间处理用, 用来记录前一个文本编号,坐标, 如果涉及文本拼接, 则记录的是拼接后保留的文本编号信息

                for item in sorted( txtlist ):
                    ox, oy = textMap[item]["o_xy"]["ox"], textMap[item]["o_xy"]["oy"]
                    if ( txtlist.index(item) == 0  ):        # 第一个不处理, 用来初始化preTxt
                        preTxt = { "id" : item, "ox" : ox, "oy" : oy }                         # 初始化preTxt 内容
                        continue

                    if ( abs( oy - preTxt["oy"] ) > 1 ): # 2个文本的y坐标差距大于1, 表示不是同一行, 跳过
                        preTxt = { "id" : item, "ox" : ox, "oy" : oy }                         # 初始化preTxt 内容
                        continue
                    
                    pre_id = preTxt["id"]
                    if ( ox >= preTxt["ox"] ):              # 留小删大
                        textMap[pre_id]['txt'] += textMap[item]['txt']
                        
                        length = self.rlen( textMap[pre_id]['txt'])
                        if ( cellIndexMap[k]["maxlen"] < length ):    # 修正最大长度, cellIndexMap[k] 列表的第一个元素用作记录最大长度
                            cellIndexMap[k]["maxlen"] = length

                        self.delTxt( item, textMap, cellIndexMap )
                    else:
                        textMap[item]['txt'] += textMap[pre_id]['txt']
                        
                        length = self.rlen( textMap[item]['txt'])
                        if ( cellIndexMap[k]["maxlen"] < length ):
                            cellIndexMap[k]["maxlen"] = length

                        self.delTxt( pre_id, textMap, cellIndexMap )
                        preTxt = { "id" : item, "ox" : ox, "oy" : oy }         # 更新ox数据
            print("-----------------处理后的textMap和cellIndexMap-----------------------------------------")
            print( textMap )
            print( cellIndexMap )
            print("----------------------------------------------------------")
        except:
            print("preProcTxtMap4Cell() Exception Error!")
            traceback.print_exc()
        
    # 15.6 preProcColRow()
    #       根据坐标关系归类到列与行, 相关信息存放在 colMap, colIndexMap, rowMap, rowIndexMap
    # 2017.01.01:
    #       为了修正表格之间的相对对齐关系, colIndexMap 调整为:
    #       {colId:{"maxlen":,"celllist":[],"subcols":[],"parentcols":[]},}
    #       这样的话, 画表格的时候就不用考虑子列的问题, 也不用考虑分隔符的数量问题了, 已经进行了修正. 唯一要修正的是:
    #           作为最后一个子列的话, 需要添加子列数-1个空格, 因为文字部分的分隔符占用是1, 父列是按2计算的.
    #       这样就补齐了.
    # 2017.01.11:
    #       rowIndexMap 修改格式: {rowid:{'cells':[],'lines':文字行数,'parent':prowid, 'sons':[]}}
    def preProcColRow( self, cellMap, cellIndexMap, colMap, colIndexMap, rowMap, rowIndexMap ):
        try:
            for k,v in sorted( cellMap.items(), key=lambda d:d[1]['y'], reverse=True) :   # 按Cell的y 坐标, 从上往下处理
                if ( k == -1 ):   # 页眉分割线不处理
                    continue
                cx, cy, cw, ch = v["x"], v["y"], v["w"], v["h"]
                col,row = {'x':cx,'w':cw}, {'y':cy, 'h':ch }
                
                key = len(colMap)+1
                if ( not col  in colMap.values() ):  # 如果该cell的x,w没有在colMap 中, 表示是新col
                    colMap[key] = col
                    maxlen = cellIndexMap[k]["maxlen"]
                    colIndexMap[key] = [ maxlen, k ]    # colIndexMap 的第一个元素是当前列的最大宽度
                    cellIndexMap[k]['col'] = key
                else:
                    for k1,v1 in sorted( colMap.items(), key=lambda d:d[0]) :
                        if ( col == v1 ):  # 找到colMap 对应的col
                            colIndexMap[k1].append(k)       # 如果对应的col 已经存在, 则在colIndexMap中添加该cell 编号即可
                            if ( colIndexMap[k1][0] < cellIndexMap[k]["maxlen"] ):   # 修正col 的最大长度
                                colIndexMap[k1][0] = cellIndexMap[k]["maxlen"]
                            cellIndexMap[k]['col'] = k1

                key = len(rowMap)+1
                if ( not row  in rowMap.values() ):  # 如果该cell的x,w没有在rowMap 中, 表示是新row
                    rowMap[key] = row
                    maxlines = len( cellIndexMap[k]["txtlist"] )
                    rowIndexMap[key] = {'cells':[k],'lines':maxlines,'parent':-1,'sons':[]}  # 'cells'中只存放cellID
                    cellIndexMap[k]['row'] = key
                else:
                    for k1,v1 in sorted( rowMap.items(), key=lambda d:d[0]) :
                        if ( row == v1 ):  # 找到rowMap 对应的row
                            rowIndexMap[k1]['cells'].append(k)       # 如果对应的row 已经存在, 则在rowIndexMap中添加该cell 编号即可
                            if ( rowIndexMap[k1]['lines'] < len( cellIndexMap[k]["txtlist"] ) ):   # 更新每行单元格的最大行数
                                rowIndexMap[k1]['lines'] = len( cellIndexMap[k]["txtlist"] )
                            cellIndexMap[k]['row'] = k1

                
            print("---------------col-----")
            print(colMap)
            print(colIndexMap)

            print("---------------row-----")
            print(rowMap)
            print(rowIndexMap)

            self.fixColMaxlen( cellIndexMap, colMap, colIndexMap, rowIndexMap )
            self.fixRows( cellMap, cellIndexMap, rowMap, colIndexMap, rowIndexMap )
            
            print("---------------col-after fixed----")
            print(colMap)
            print(colIndexMap)

            print("---------------row--after fixed----")
            print(rowMap)
            print(rowIndexMap)
        except:
            print("preProcColRow() Exception Error!")
            traceback.print_exc()


    # 15.61 fixColMaxlen()
    #      修正cell的最大长度.
    # 说明:
    #      目前的单元格的最大长度是同列的最长字符串长度(汉字算2个).
    #      有时候该列内有可能有多个子列. 那么多个子列内的最大长度之和有可能会超过父列最大字符串长度
    #      按行顺序来依次处理列
    #
    #      不行, 上面的实现方式还是有很多缺陷. 现在简要处理, 循环处理所有行, 获取最大的长度行的长度(也就是getRowSplitPos()后最后一个元素值最大).
    #      然后所有的行的最大值都设成这个值即可. 即最后一个元素都设置为该值即可.
    # 2017.01.01:
    #      修正复杂表格的对齐暂时放弃. 很复杂, 不是简单调整能完成.
    #      从width最短的col开始处理, 然后所有行轮训, 察看是否有subcol，
    #      如果有, 就计算subcol 长度之和与分隔符数量, 然后修正最大长度.
    def fixColMaxlen( self, cellIndexMap, colMap, colIndexMap, rowIndexMap ):
        try:
            for colId, v in sorted( colMap.items(), key=lambda d:d[1]['w']):    # 按列的 实际宽度来排序, 从最窄到最宽
                colx, colw = colMap[colId]["x"], colMap[colId]["w"]
                colx2 = colx + colw
                # 1. 按行循环处理, 寻找该col在 同行的子列.
                for rk,rv in sorted( rowIndexMap.items(), key=lambda d:d[0] ):
                    cellList = rv["cells"]                   # 行的cell列表

                    # 1. 循环处理 cell, 判断该cell 所在列的最大长度是否已经是真实的最大, 如果有子列之和大于该cell的maxlen就用子列之和更新为最大长度
                    subcols = []
                    for cellId in cellList:
                        subcolId = cellIndexMap[cellId]["col"]    # 获取该cell 所在的colID
                        
                        if ( subcolId == colId ):               # 该cell所在列就是要处理的列, 则跳过
                            continue
                            
                        subcolx, subcolw = colMap[subcolId]["x"], colMap[subcolId]["w"]
                        subcolx2 = subcolx + subcolw
                        #print("行[%d]可能的子列%d(x=%.3f, w=%.3f)" % (rk, subcolId, subcolx,subcolw ) )
                        if ( subcolx >= colx and ( subcolx2 < colx2 or abs(subcolx2 -colx2) < 1 )): # 用abs() 的原因是python 中浮点数计算会有误差, 对于画布坐标而言, 小于1个像素认为是相同位置
                            subcols.append(subcolId)

                    #print("===========-col=%d(x=%.3f,w=%.3f)的子列有:" % (colId, colx, colw) )
                    #print(subcols)
                    # 2. 获取所有子列的最大长度之和, 并加上分隔符长度(一个分隔符占位为2), 然后与当前列最大长度比较
                    subcolsum = len(subcols)
                    if( subcolsum == 0 ):                   # 如果没有子列或只有一个子列, 就继续处理下一个col
                        continue

                    newMaxLen = 0
                    for item in subcols:       # 这儿Python 有个Bug, 如果用了上面循环里的subcolId, 取值就出现了混乱
                        subcollen = colIndexMap[item][0]
                        newMaxLen += subcollen

                    if ( subcolsum > 1 ):
                        #print("加分隔符之前的长度%d" % newMaxLen)
                        newMaxLen += (subcolsum-1)*1  # 分隔符占1？？ 应该是2呀, 但是在txt中显示就是占1, 虽然用rlen()计算出来是2。。。。
                        #print("加分隔符之后的长度%d" % newMaxLen)

                    if ( colIndexMap[colId][0] <= newMaxLen ):
                        colIndexMap[colId][0] = newMaxLen
                    else:
                        # 如果子列的最大宽度之和小于父列, 需要进一步判断最后一个子列的是否与父列的x+w是否相同,
                        # 如果相同, 修正最后一个子列的maxlen, 也就是对齐
                        lastcolId = subcols[-1]
                        lastcolx, lastcolw = colMap[lastcolId]["x"], colMap[lastcolId]["w"]
                        if ( lastcolx + lastcolw == colx+colw ):    # 对齐的, 补齐
                            colIndexMap[lastcolId][0] += colIndexMap[colId][0] - newMaxLen
                    
        except:
            print("fixCellMaxlen() Exception Error!")
            traceback.print_exc()
        return

    #  15.62 fixRows()
    #      修正某些行本身又带有自行的情况, 比如中间的一个单元格可能是上下两个单元格, 参见0106  300182捷成股份2016年度业绩预告
    #  思路:
    #     2017.01.10:
    #         rowIndexMap 修正. 按子行的多少来扩充母行中没有自行的单元格, 但是显示的时候, 不显示对应的线.
    #          ┌-------------------┬----------------┬----------------------------┐
    #          |         1         |    2           |   3                        |
    #          ├-------------------┼----------------┼----------------------------┤
    #          |                   |       5        |                            |
    #          |      4            |                |          7                 |
    #          |                   ├----------------┤                            |
    #          |                   |        6       |                            |
    #          └-------------------┴----------------┴----------------------------┘
    #         上面的row 应该有4行, 分别为: row1: [1,2,3], row2 = 4, 7, row3,row4;  row 2 = 5, row3 = 6 修正如下
    #         row1 = [1,2,3], row3={cells=[4,5,7],parent="2"}, row4={cells=[4,6,7],parent="2"},  row2= {[4, 7], "sons"=[row3, row4]}
    #         也就是说, 有son的row不用显示,
    #         有parent的row 显示的时候要3个工作
    #          1. 是否是子行中的第一行, 也就是y最大的一行. 如果是, 则所有分割线要显示, 也就是cell是否在parent不重要
    #          2. 判断cell是否在parent中, 如果有, 该cell对应的连线不处理
    #          rowMap = {1: {'h': 78.0, 'y': 561.42}, 2: {'h': 31.2, 'y': 379.16}, 3: {'h': 27.0, 'y': 351.68}, 4: {'h': 54.48, 'y': 324.2}}
    #          rowIndexMap={1: [2, 7], 2: [2, 1, 2, 3], 3: [1, 5], 4: [2, 4, 6]}
    #     2017.01.11:
    #          rowIndexMap = {1:{"cells":,"lines":,"parent":,"sons":}}
    #          
    def fixRows( self, cellMap, cellIndexMap, rowMap, colIndexMap, rowIndexMap ):
        tableDict = {'left_top':'┌', 'mid_top':'┬', 'right_top':'┐', 'mid_left':'├', 'mid_mid':'┼',
                     'mid_right':'┤', 'left_bottom':'└', 'mid_bottom':'┴', 'right_bottom':'┘',
                     'rowline':'─', 'colline':'│'}
        try:
            for k,v in sorted( rowMap.items(), key=lambda d:d[1]['h']):   # 按row 的h 坐标从小往大处理处理, 也就是如果有子行, 一定会包含进去的.
                y, h = v['y'], v['h']
                               
                # 0. 如果已经有母行就不判断了, 继续处理后面的, 也就是说每个子行只有一个母行, 而且是最小的母行
                if ( rowIndexMap[k]["parent"] != -1 ):   # -1 是初始化的值, 如果不是-1, 表示已经有母行了
                    continue
                               
                # 1. 循环查询其他行, 看看有没有母行
                for k1,v1 in sorted(rowMap.items(), key=lambda d:d[1]['h']):
                    if ( k == k1 ):      # 同一行不处理
                        continue
                    y1, h1 = v1['y'], v1['h']
                    # 2. 判断是否是母行
                    
                    if ( ( y >= y1 or abs(y-y1) < 1 )  and ( (y+h)<=(y1+h1) or abs(y1+h1-y-h) < 1 ) ): # abs 的判断是因为子行和母行上面边或下面边重叠的时候, 坐标有可能不是完全相同, 有可能有微小误差
                        print("--$$--%d 是 %d 的子行---" % (k, k1))
                        rowIndexMap[k]["parent"] = k1
                        rowIndexMap[k1]["sons"].append(k)   # 有可能有多个子行
                        # 2.1 子行的cells中添加母行的cells, 这样后面画表的时候就可以进行处理了. 注意, 要对cell进行x坐标排序加入列表, 否则顺序就错了
                        c1, c2, = rowIndexMap[k]["cells"], rowIndexMap[k1]["cells"]
                        c3, c4  = sorted(set( c1 + c2)), []

                        # 下面的循环实际上是个排序过程, 因为循环的条件就是排好序的
                        for k2, v2 in sorted( cellMap.items(), key=lambda d:d[1]['x']):  # 遍历一边所有的cell, 按照x从小往大处理
                            if ( k2 in c3 ):  # 如果cellMap 中的cellID 在合并后的cell列表c3中,则添加到c4中
                                c4.append(k2)

                        rowIndexMap[k]["cells"] = c4  
                        # 说明: 由于cell 是优先归属于y比较大的行, 所以, 子行中的cell不会归属于母行的cells中
                        break                               # 找到第一个母行就行了. 这个母行是高度最小的

                # 2. 修正本行的行数
                sons = rowIndexMap[k]['sons']
                if ( len(sons) != 0 ):
                    maxlines = 0
                    for rowid in sons:
                        maxlines += rowIndexMap[rowid]['lines']
                    if ( maxlines > rowIndexMap[k]["lines"] ):
                        rowIndexMap[k]["lines"] = maxlines
                                    
                # 3.不用修正当前母行行数. 母行在循环中也会被处理到, 不用嵌套处理

        except:
            print("fixRows() Exception Error!")
            traceback.print_exc()
        return

    # 15.7 buildTableMap()
    #       解析文本与cell的关系, 拆分出table 出来, 创建tableMap={1:[cellid_list]}， 同时在cellMap 中添加tableid 属性
    # 2017.01.10:
    #     更改实现方式, 循环按照 oy 坐标从上往下处理
    def buildTableMap( self, textMap, cellMap, cellIndexMap, tableMap, colIndexMap, rowIndexMap  ):
        try:
            flag, key = False, 1   # key 放在这儿是为了循环里面多处会访问
            cellProced=[]    # 记录已经处理过的cell, 如果当前文本所在的cell已经被处理过了, 则跳过
            for k, v in sorted( textMap.items(), key=lambda d:d[1]['o_xy']['oy'], reverse=True ):
                if ( v['cell'] == -1 ):  # 跳过不在单元格里面的文本
                    if ( flag ):                # 如果之前正在处理表格, 那么现在就是表格处理结束了, flag 置为False, 表示不是表格处理了
                        flag = False    # 重置
                    continue

                if ( v['cell'] in cellProced ):    # 已经处理过的单元格不再处理
                    continue
                
                ox, oy = v['o_xy']['ox'], v['o_xy']['oy']
                pre_id = v['pre']
                cellid = textMap[k]['cell']

                cellProced.append( cellid )     # 记录被处理过的cell, 这样碰到多行文字的单元格就只处理一次
                
                row, col, tbkey = cellIndexMap[cellid]["row"], cellIndexMap[cellid]["col"], -1
                if ( not flag ):    #不是在处理表格, 那么下面就是表格, 是表格的第一个cell
                    tbkey = len(tableMap)+1
                    # 第一个用来记录本表最后用到的txt编号, 用来显示文本的时候进行处理
                    lasttxtid = cellIndexMap[cellid]["txtlist"][-1]
                    tableMap[tbkey] = {"cells":[cellid],"rows":[row], "cols":[col],'lasttxtid':lasttxtid}    # cells 第一个元素用来记录最后一个文本      
                    cellIndexMap[cellid]['table'] = tbkey
                    flag = True                     # 表示正在处理表格
                else:         # 已经在处理表格了, 那么这个cell仍然是table 的一部分
                    tbkey=len(tableMap)     # 不是新建的,不用+1
                    if ( cellid in tableMap[tbkey]['cells'] ):    # 如果该cell已经处理过了就不处理了
                        continue
                    tableMap[tbkey]["cells"].append( cellid )
                    cellIndexMap[cellid]['table'] = tbkey
                    tableMap[tbkey]["lasttxtid"] = cellIndexMap[cellid]["txtlist"][-1] 
                    if ( row not in tableMap[tbkey]['rows']):
                        tableMap[tbkey]['rows'].append(row)
                    if ( col not in tableMap[tbkey]['cols']):
                        tableMap[tbkey]['cols'].append(col)

            print('----------------表格信息-----------------------')
            print(tableMap)
            print(cellMap)
            print(cellIndexMap)
        except:
            print("buildTableMap() Exception Error!")
            traceback.print_exc()
            
                    
    # 15.8 buildPageTxt()
    #     输出当前页纯文本, 带表格格式. 已经处理过同行多文本的拼接, 不再cell中的文本就是单独一行文本
    #2017.01.10:
    #     不能按照text 编号顺序处理, 应该按照oy 坐标从上往下处理.
    # 2017.02.09:
    #     把表格内容存放在哈希表 sheetMap = {表编号:"表的内容(文字及分隔符)",} 表编号从1开始
    def buildPageTxt( self, textMap, cellMap, cellIndexMap, tableMap, colIndexMap, rowIndexMap ):
        
        retbuf = ""
        tbl_rec = []    # 记录已经处理过的表格, 用来判断当前文本是否已经处理了
        try:
            if ( len( textMap ) == 0 ):   # 如果textMap 是空的, 可能前面的处理有问题, 没有获得文本
                return

            for k,v in sorted( textMap.items(), key = lambda d:d[1]['o_xy']['oy'], reverse=True ):  # 按oy 坐标, 从上往下处理
                cellId = v['cell']
                if ( cellId == -1 ):   # 不在cell中的文本本身就是单独一行, 因为之前已经处理过文本了
                    # 这儿增加一个过滤操作, 把仅仅是空格的行过滤掉, 否则下面添加两个换行就会产生非常多的空行
                    if ( len( v['txt'].strip() ) != 0 ):
                        retbuf += v['txt'] + '\r\n\r\n'
                else:  # 表格处理
                    tableid = cellIndexMap[cellId]['table']
                    if tableid in tbl_rec:
                        continue
                    tblcontent = self.buildTableTxt( textMap, tableMap[tableid], cellMap, cellIndexMap, colIndexMap, rowIndexMap )
                    retbuf += tblcontent
                    # 2017.02.14 : 把表格存放到哈希表 sheetMap中, 下标从1开始, 该表存放的处理过的所有页中的表格
                    l = len( self.sheetMap )
                    self.sheetMap[l+1] = tblcontent
                    tbl_rec.append(tableid)

            return retbuf
        except:
            print("buildPageTxt() Exception Error!")
            traceback.print_exc()
            return retbuf

    # 15.9 buildTableTxt()
    #      将表格里面的文本格式化输出
    #  table       {"rows":, "cols":,"cells":,}
    #  实现思路:
    #      1. 找到cell_list 中的第一个cellID, 然后处理该cellID所在的row，以及row 涉及的所在col
    #      
    def buildTableTxt( self, textMap, table, cellMap, cellIndexMap, colIndexMap, rowIndexMap ):
        retbuf = ""
        try:
            rows, cols, cells = table["rows"].copy(), table["cols"].copy(), table["cells"].copy()
            print("------------------------table.rows...........")
            print(rows)
            flag = False     # 是否是表头的标志
            for item in rows:      # item 是行号, rows 的行是按照 y 坐标从大到小排列的, 也就是从上往下
                print("rowid=%d" % item)
                if ( len( rowIndexMap[item]['sons'] ) > 0 ):    # 有子行的话就不处理了, 子行处理顺带处理的母行的部分
                    continue
                if ( not flag ):  # 如果没有建表头, 需要建表头
                    retbuf += self.buildRowHeader( rowIndexMap, colIndexMap, item, textMap, cellMap, cellIndexMap )
                    flag = True
                else:
                    # 建表中隔线
                    #retbuf += "├──────────┼────┼────┼────┼────┼────┤ "
                    retbuf += self.buildRowSplit( rowIndexMap, colIndexMap, item, cellMap, cellIndexMap )
                    
                retbuf += self.buildRowBody( rowIndexMap, colIndexMap, item, textMap, cellMap, cellIndexMap )

            # 表格最下面的线
            lastRowId = rows[-1]
            while ( len( rowIndexMap[lastRowId]['sons'] ) > 0 ):   # 如果最后一行有子行, 那么就处理该行的最后一个子行
                lastRowId = rowIndexMap[lastRowId]['sons'][-1]
            retbuf += self.buildRowFooter( rowIndexMap, colIndexMap, lastRowId, cellMap, cellIndexMap )
        except:
            print("buildTableTxt() Exception Error!")
            traceback.print_exc()
        return retbuf

    # 15.10 buildRowHeader()
    #      将表格里面的文本格式化输出
    # getRowSplitPos
    # 2017.01.11:
    #      修正实现方式, 根据新的rowIndexMap ={'cells':,'lines':,'parent':,'sons':[]}来进行处理
    #      只处理子行, 母行不用处理, 因为处理子行的时候顺便就把母行的内容处理了.
    #      header 的处理简单处理, 直接按照子行中的所有cell来进行处理(包含母行)
    #      也就是说实现方式其实没有改变.
    def buildRowHeader( self, rowIndexMap, colIndexMap, rowID, textMap, cellMap, cellIndexMap ):
        retbuf = ""
        try:
            # ┌──────────┬────┬────┬────┬────┬────┐
            tableDict = {'left_top':'┌', 'mid_top':'┬', 'right_top':'┐', 'mid_left':'├', 'mid_mid':'┼',
                         'mid_right':'┤', 'left_bottom':'└', 'mid_bottom':'┴', 'right_bottom':'┘',
                         'rowline':'─', 'colline':'│'}
            if ( len(rowIndexMap[rowID]['sons']) != 0 ):     # 如果不是子行, 则 直接放回, 不进行处理
                return ""
            curRowSplitPos = self.getRowSplitPos( rowIndexMap, colIndexMap, cellIndexMap, rowID )
            print( curRowSplitPos )
            col_sum = len(curRowSplitPos) - 1       # 减去1 因为第一个是坐标数,减去1才是列数, 第一个坐标是0

            retbuf = tableDict['left_top']
            for i in range(0,col_sum):
                if ( i == 0 ):  # i = 0 对应第一个col，
                    col_len = curRowSplitPos[i+1]
                else:
                    col_len = curRowSplitPos[i+1] -curRowSplitPos[i]- 1     # 实际长度要减去之前的分隔符所占的2才是真正的连线长度， 因为每一列都修正, 所以只减2
                if ( i != col_sum-1 ):  # 如果不是最后一列, 就用rowline+midt_op
                    retbuf += col_len * tableDict['rowline'] + tableDict['mid_top']
                else:
                    retbuf += col_len * tableDict['rowline'] + tableDict['right_top']
            retbuf += '\r\n'
            print("-----row header----")
            print(curRowSplitPos)
            print(retbuf)
        except:
            print("buildRowHeader() Exception Error!")
            traceback.print_exc()

        return retbuf

        
    # 15.11 buildRowBody()
    #      将表格里面的文本格式化输出
    #  
    def buildRowBody( self, rowIndexMap, colIndexMap, rowID, textMap, cellMap, cellIndexMap ):
        retbuf = ""
        try:
            # ┌──────────┬────┬────┬────┬────┬────┐
            tableDict = {'left_top':'┌', 'mid_top':'┬', 'right_top':'┐', 'mid_left':'├', 'mid_mid':'┼',
                         'mid_right':'┤', 'left_bottom':'└', 'mid_bottom':'┴', 'right_bottom':'┘',
                         'rowline':'─', 'colline':'|', "body_left":"│", "body_right":"│" }
            # 1. 先取该行的列数与单元编号, rowIndexMap[rowId]['cells']是个列表   [cellid1,cellid2...]
            cols = len( rowIndexMap[rowID]['cells'] ) #  几个单元格就是几列
            lines = rowIndexMap[rowID]["lines"]
            print(" cols=%d, lines=%d, rowid=%d" % (cols, lines, rowID))
            for i in range(0, lines):    #外循环是行
                retbuf += tableDict['body_left']
                for j in range(0,cols):         # 内循环是列,
                    retbuf += self.getCellLineText( rowID, j, i, rowIndexMap, colIndexMap, cellMap, cellIndexMap, textMap )

                    if ( j == cols-1 ) :   # 如果是最后一列, 用body_right， 否则用colline
                        retbuf += tableDict['body_right']
                    else:
                        retbuf += tableDict['colline']
                        
                retbuf += '\r\n'
            print("-----row header----")
            print(retbuf)
        except:
            print("buildRowBody() Exception Error!")
            traceback.print_exc()
            retbuf= ""
        return retbuf
        
    # 15.12 getRowSplitPos()
    #      获取指定行的分割线位置
    #      第一个元素0 是为了方便计算列长, retlist[i] - retlist[i-1] 就是实际的列长
    def getRowSplitPos( self, rowIndexMap, colIndexMap, cellIndexMap, rowID ):
        retlist = [0]
        try:
            cols = len( rowIndexMap[rowID]["cells"] )
            col_pos = 0
            for i in range( 0, cols ):
                cellId = rowIndexMap[rowID]['cells'][i]          # rowIndexMap[rowID]的第0个元素是最大行数
                colId = cellIndexMap[cellId]['col']
                col_len = colIndexMap[colId][0]            # 当前列的最大宽度
                if ( i == 0 ):
                    col_pos = col_len
                else:
                    col_pos += col_len  + 1           # 加 1 是为了 修正分隔符所占的2位, 因为每一个都进行修正, 这样只需要加一次即可, 保证本次是真实的位置即可.以后的也只需要加一次
                retlist.append( col_pos )
        except:
            print("getRowSplitPos() Exception Error!")
            traceback.print_exc()
        return retlist

    # 15.13 getCellLineText()
    #       获取指定cell内的指定行的文本
    #  注意, colNo 不是 列编号, 而是该行表格的列号, 比如该行的第1列,第2列, 实际对应的列编号, 可能是colIndexMap 中的18,19等.
    # 2017.01.12:
    #     修正母行的文字获取, 如果是母行的cell, 则文字的行号是当前子行之前的所有子行行号之和+1
    # 2017.01.15:
    #     如果 获取后的文字包含表格连接线'rowline':'─', 注意这个不是横线'-'. 连接线虽然占位是2, 但是在文本中显示的时候却是1格.
    # 所以如果要修正txt中的显示, 需要做些修改, 也就是说有几个'rowline':'─', 应该加几个空格来补全.
    def getCellLineText( self, rowId, colNo, lineNo, rowIndexMap, colIndexMap, cellMap, cellIndexMap, textMap ):
        
        retbuf = ""
        try:
            cellId = rowIndexMap[rowId]['cells'][ colNo ]   # 
            colId = cellIndexMap[cellId]['col']
            col_len = colIndexMap[colId][0]            # 当前列的最大宽度
            rlineNo = lineNo

            # 修正lineNo
            parent = rowIndexMap[rowId]['parent']
            if ( parent != -1 and cellId in rowIndexMap[parent]['cells']):     # 有母行的情况下, 如果正好处理的是母行的cell, 则要修正文字对应的行号
                for item in rowIndexMap[parent]['sons']:
                    if ( item == rowId ):  # 到当前行就跳出
                        break
                    rlineNo += rowIndexMap[item]['lines']
            cell_lines = len(cellIndexMap[cellId]["txtlist"])     # 所有的元素个数就是该cell的文本行数, 每一个文本就是一行
            print("==##==cellId=%d, colId=%d, col_len=%d, cell_lines=%d, lineNo=%d" % (cellId, colId, col_len, cell_lines, lineNo) )
            if ( rlineNo < cell_lines ) :                     # 如果该cell的行数小于最大行数, 不够的就用空格替代， lineNo 是从0开始的
                txtId = cellIndexMap[ cellId ]["txtlist"][rlineNo]
                txt = textMap[txtId]['txt']
                blank_len = col_len - self.rlen(txt)
                retbuf += txt + blank_len * " "
                #print("=======getCellLineText()===colNo=%d,lineNo=%d,txt=%s" % (colNo, lineNo, txt))
            else:
                retbuf += col_len * " "
        except:
            print("getCellLineText() exception Error!")
            traceback.print_exc()
        return retbuf

    # 15.141 getRealPreRowID( rowIndexMap, rowID)
    #      获取真正的"前一行", 局部方法
    #      缺省的前一行就是行号减一, 但是由于有可能是母行, 所以要进一步进行判断
    #      由于生成rows， rowIndexMap 的时候是按照y 坐标顺序从上往下处理的, 所以子行的前一行永远不可能是该子行的母行
    def getRealPreRowID( self, rowIndexMap, rowID ):
        preRowID = rowID - 1
        try:
            while( len( rowIndexMap[preRowID]["sons"] ) > 0 ):  # 如果是母行就循环处理, 直到获得母行的最后一个子行
                preRowID = rowIndexMap[preRowID]['sons'][-1]
        except:
            print("getRealPreRowID() Exception Error!")
            traceback.print_exc()
            preRowID = -1
        return preRowID
    # 15.14 buildRowSplit()
    #      创建表格的行之间的分隔线
    # 2017.01.11:
    #      更改实现方式, rowIndexMap={'cells':,'lines':,'parent':,'sons':}
    #      调用这个方法之前已经确认这个就是子行了，
    #      获取的前一行要进一步判断是否是同一parent的子行, 如果不是, 需要进一步判断有子行,
    #      嵌套处理, 获取最后一个子行, 这个子行才是真正的"前一行"
    def buildRowSplit( self, rowIndexMap, colIndexMap, rowID, cellMap, cellIndexMap ):
        tableDict = {'left_top':'┌', 'mid_top':'┬', 'right_top':'┐', 'mid_left':'├', 'mid_mid':'┼',
                     'mid_right':'┤', 'left_bottom':'└', 'mid_bottom':'┴', 'right_bottom':'┘',
                     'rowline':'─', 'colline':'|', "body_left":"│", "body_right":"│" }
        
        retbuf = ""
        try:
            
            cols = len( rowIndexMap[rowID] ) -1 #  几个单元格就是几列, -1 是因为第一个元素是行数

            # 1. 获取真正的"前一行"
            preRowID = self.getRealPreRowID( rowIndexMap, rowID )
            
            parent = rowIndexMap[rowID]['parent']
            curRowSplitPos = self.getRowSplitPos( rowIndexMap, colIndexMap, cellIndexMap, rowID )

            print("parent =%d,rowIndexMap[preRowID]['parent']=%d" % (parent, rowIndexMap[preRowID]['parent']))
            if ( parent == -1 or  parent != rowIndexMap[preRowID]['parent'] ):
                retbuf = tableDict["mid_left"]            # "├"
                # 2.1 本行是单独一行或者第一个子行, 正常处理, 没有需要省略的连接线
                preRowSplitPos = self.getRowSplitPos( rowIndexMap, colIndexMap, cellIndexMap, preRowID )
                
                allSplitPos = sorted(set( preRowSplitPos + curRowSplitPos ))
                len_all = len( allSplitPos )

                print("--------pre,cur, all-------pos-")
                print(preRowSplitPos)
                print(curRowSplitPos)
                print(allSplitPos)

                flag1,flag2 = False, False  # 值为True时表示该行结束. flag1表示上一行, flag2表示当前行(位操作效率更高,但是可读性不如2个变量)
                # 这儿需要注意,  preRowSplitPos=[0 22 42], cur..=[0 22 37 52 67]  all = [0, 22, 37, 42, 52, 67]
                # 那么对pre的第二个cell而言, 连接线及分隔符长度应该是: 42-22+1=21, 但是用all 计算的时候: 37-22+1+(42-37+1)=16+6=22， 也就是37所占的分隔符计算了2次
                #  应该减去37对应的分隔符一次. 也就是说删除的是相邻两个cell之间多余计算的分隔符部分
                for i in range(1, len_all ):        # i == 0的时候就是位置0, 用来方便后续计算控制用的, 没有实际意义
                    curPos = allSplitPos[i]
                    con_len = allSplitPos[i] - allSplitPos[i-1]
                    if ( i != 1 ):      # 第一列不需要修正分隔符的占位, 其他行都要修正
                        con_len -= 1    # 计算连线距离, 减去1是为了修正连线不包括分隔符的占位1, 因为前面的位置也修正过了, 所以这儿只需要减1即可

                    print("buildRowSplit(), 独立一行或第一子行, curpos=%d, con_len=%d,:%s:" % (curPos, con_len, retbuf) )
                    flag1, flag2 = (curPos == preRowSplitPos[-1]), (curPos == curRowSplitPos[-1])  # 逻辑判断结果赋值
                        
                    if (  curPos in preRowSplitPos and curPos in curRowSplitPos ): # 两行都有
                        retbuf += con_len * tableDict['rowline'] 
                        if ( not flag1 or not flag2 ) :   # 只要有一行没结束, 无论另一行是否结束, 对于两行都有的情况, 用'mid_mid':'┼'
                            retbuf += tableDict['mid_mid']                         # '-----┼'
                        else:                                    # 2行都结束, 即 flag1和flag2 都是True 用   '-----┤'
                            retbuf += tableDict['mid_right']                    # '-----┤'
                    else: #    不是两行同时有的情况
                        if ( curPos in preRowSplitPos ) :    # 在上一行
                            retbuf += con_len * tableDict['rowline']    # 属于上一行的分隔符, 减去之前的当前行的分隔符数量
                            if ( not flag1 ):  # 上一行没结束, 无论下一行是否结束, 都是'------┴'
                                retbuf += tableDict['mid_bottom']
                            elif ( flag1 and not flag2 ):   # 上一行结束了, 但是下一行没结束, 也用'------┴'
                                retbuf += tableDict['mid_bottom']
                            else:  # 2行都结束了, 但是最后是上一行, 因为外围的判断是上一行, 用'------┘' 也就是说下一行早就结束了
                                retbuf += tableDict['right_bottom']
                        else:          # 不在上一行就是当前行
                            retbuf += con_len * tableDict['rowline'] 
                            if ( not flag2 ):  # 当前行没结束, 无论上一行是否结束, 都是'------┬'
                                retbuf += tableDict['mid_top']
                            elif ( flag2 and not flag1 ):   # 当前行结束了, 但是上一行没结束, 也用'------┬'
                                retbuf += tableDict['mid_top']
                            else:  # 2行都结束了, 但是最后是当前行, 因为外围的判断是上一行, 用'------┐'
                                retbuf += tableDict['right_top']
            else:                   # 本行是单独一行, 没有母行, 正常处理, 没有需要省略的连接线
                # 2.2 是子行, 并且不是第一个子行, 需要省略母行中cell对应的连接线. 判断子行中的cell成员, 如果在母行中,
                #  那么就省略连接线,  直接用 |, 第一个不再母行中的cell， 用 ├, 最后一个用┤
                #  因为是第二个子行, 位置信息不会发生变化, 也就是与上一行相同, 就不用像上面那么复杂判断了
                cur_cells = rowIndexMap[rowID]['cells']
                par_cells = rowIndexMap[parent]['cells']
                len_cur = len( curRowSplitPos )
                print("buildRowSplit(), 其他子行,len_cur=%d" % (len_cur))
                print(cur_cells)
                print(par_cells)
                for i in range(1, len_cur ):    # i == 0的时候就是位置0, 用来方便后续计算控制用的, 没有实际意义
                    col_len = curRowSplitPos[i] - curRowSplitPos[i-1]
                    print("col=%d,宽度=%d" % (i,col_len))
                    print(curRowSplitPos)
                    if ( i != 1 ):
                        col_len -= 1
                        
                    if ( cur_cells[i-1] in par_cells ):     # 当前cell是母行的, 没有连接线, cur_cells 的下标从0开始的
                        if ( i == 1 or ( cur_cells[i-2] in par_cells ) ):  # 前一个cell 是母行的话, 需要应该用"│     "
                            retbuf += "│" + col_len * " "
                        else:                               # 前一个cell 不是母行的话, 需要应该用"┤     "
                            retbuf += "┤" + col_len * " "
                    else:                                   # 当前cell是子行的, 有连接线
                        if ( i == 1 or ( cur_cells[i-2] in par_cells ) ):  # 前一个cell 是母行的话, 需要应该用"├     "
                            retbuf += "├" + col_len * "─"
                        else:                               # 前一个cell 不是母行的话, 需要应该用"┼     "
                            retbuf += "┼" + col_len * "─"
                    # 最后一个cell判断
                    if ( i == len_cur-1 ):
                        if ( cur_cells[i-1] in par_cells ): # 如果是母行的, 结束符是"|"
                            retbuf += "│"
                        else:
                            retbuf += "┤"
                
            retbuf += '\r\n'
            print("-----------分割线为-------")
            print(retbuf)
        except:
            print("buildRowBody() Exception Error!")
            traceback.print_exc()
            retbuf= ""
        return retbuf

    # 15.15 buildRowFooter()
    #      将表格里面的文本格式化输出
    def buildRowFooter( self, rowIndexMap, colIndexMap, rowID, cellMap, cellIndexMap ):
        retbuf = ""
        tableDict = {'left_top':'┌', 'mid_top':'┬', 'right_top':'┐', 'mid_left':'├', 'mid_mid':'┼',
                     'mid_right':'┤', 'left_bottom':'└', 'mid_bottom':'┴', 'right_bottom':'┘',
                     'rowline':'─', 'colline':'|', "body_left":"│", "body_right":"│" }

        print("================buildRowFooter() Begin")
        retbuf = '└'            # '└'
        try:
            curRowSplitPos = self.getRowSplitPos( rowIndexMap, colIndexMap, cellIndexMap, rowID )
            print("================buildRowFooter() curRowSplitPos")
            print(curRowSplitPos)

            len_cur = len( curRowSplitPos )

            for i in range(0, len_cur ):
                if ( i == 0 ):      # i == 0的时候就是位置0, 用来方便后续计算控制用的, 没有实际意义
                    continue

                con_len = curRowSplitPos[i] - curRowSplitPos[i-1]     # 计算连线距离
                if ( i != 1 ):  # 修正
                    con_len -=  1    

                retbuf += con_len * tableDict['rowline']
                
                if ( i != len_cur-1 ):      # 不是最后一个
                     retbuf += '┴'
                else:
                     retbuf += '┘'
            retbuf += '\r\n'
            print("-----row footerer----")
            print(curRowSplitPos)
            print(retbuf)
        except:
            print("buildRowFooter() Exception Error!")
            traceback.print_exc()
            retbuf= ""
        return retbuf
