# -*-  coding: utf-8  -*-

# pdf操作工具
# 深红的报复之盾 火眼人
# 坐标系的原点:  左上角是(0,0)
# 1. parsePDF()  -- getStartxrefPos(), getxref(), getPages(), getCmapList, getCMAPs()
# 2. getStartxrefPos()
# 3. getxref()  ---- getTrailer()
# 4. getTrailer()
# 5. getPages()  --- getObjContent(), getPageleaf()
# 6. getObjContent()
# 7. getPageleaf()
# 8. getCmapList() ---- getObjContent(),isType0()
# 9. isType0()
# 10. getCMAPs() -----getObjContent(), getItemOfObj(),procType0Stream()
# 11. getItemOfObj() -- getObjContent
# 12. procType0Stream() ---  getItemOfObj(), decompress()
# 13. decompress() --- import zlib(zlib.decomporess())
# 14. processPage() ---- getItemOfObj()
##########################################
#     下面的方法全部都是处理内容的, 包括解码, 格式调整等
#  2016.12.21:
#      删除了IFCTRL1() 判断换行的实现方式不再用之前的方法.
# 15. decode()---  file_tools.initStreamBuf(), .readLineST( streambuf)
#                  self.processBT(), .processBDC()
# 16. processBT() -- self.processBDC(), .processRE(), /*processQ()*/
#                    self.hasTxtPosition(), .processTxtPosition(),  .hasText(), .processText(),
#                    file_tools.readLineST()
# 17. processBDC() -- self.processBT(), .processRE(), /*processQ()*/
#                    self.hasTxtPosition(), .processTxtPosition(),  .hasText(), .processText(),
#                    file_tools.readLineST()
# 18. hasText()
# 19. processText()---  self.ifCRLF(), .processTj(), .processTJ()
# 20. processTj() --- none
# 21. processTJ() ---
# 23. processRE()
# 24. processQ()
# 25. hasTxtPosition()
# 26. precessTxtPosition()
# 27. processTd()
# 28. processTD()
# 29. getOriginXY()
# 30. processTm()
# 31. processTstar()
# 99. rlen()


import zlib
import re
import sys
import traceback
from file_tools import util_fileService

class pdfService():

    def __init__(self):
        self.tmpfile1 = "f:/F_T_tmp/tmp1/tmp.txt"
        self.file_tools = util_fileService()
        self.xref = {}
        self.pages = {}

    ####################################################
    # W 开头的方法属于外部接口
    # W1. getSpecKeyLine()
    #     获取指定关键字所在的行, 只返回第一个包含指定关键字的行
    def getSpecKeyLine():
        return
    '''
     * 解析 PDF文件， 参见: Java/senior/pdf文件
     * 1. parsePDF()
     *
     * 2016.05.01  
     *          从 util_fileService 中拆分出来，主要处理步骤如下:
     *      1. 获取PDF 文件的trailer, 调用getTrailer()
     *      2. 对xref 进行预处理。由于采用多线程机制来提高处理效率， 可以先把部分重要
     *      的信息通过预处理先获得：preGetxref()
     * 2016.05.07:
     *      原来的解析方法有缺陷，xref 的处理有问题, 进行改进。每个xref都有一个trailer。
     *      1. 废弃 preGetxref(), 使用新的getxref(), 
     *      2. 废弃getTrailer(), 使用 getTrailerx(), 这个方法仅在 getxref()中使用.
     *      3. 解析步骤为:
     *          a. 获取xref. --> getxref() { gettrailerx() }
     *          b. 根据Root 获取pages 最初的对象列表
     *          c. 处理 pages 获取所有的叶子节点, 也就是有内容的页面对象 pagetree
     *             同时获取 对应的cmaplist, "页号":"cmap1 cmap2", 这个页号与pagetree
     *             中的key值是一致的, 也就是实际的页号。 需要注意的是, cmaplist中的第一个
     *             元素: "total" 内容是所有的cmap 综合， 便于后续处理将所有的cmap 内容获取出来.
     *          d. 获取所有的cmap对象的内容。 解码后进行解析， 将映射表处理成哈希表作为
     *             cmaps 哈希表的value.    即: "cmap对象编号":哈希表(映射表实际内容)
     *          e. 解析指定页面的内容.  这个是为了提高处理效果， 不用全部解析， 不然性能极低。 
     *             
     * 调用的外部方法有:
     *      1. initReadFileMap() -------------->util_fileService
     * 调用的类对象内部的方法有:
     *      1. getStartxrefPos()
     *      2. getxref()
     *      3. getPages()
    '''
    def parsePDF( self, srcFile, pageno ):

        self.file_tools.initReadFileMap( srcFile )
        
        trailer, posmap = {}, {}

        # 获取startxref 的内容, 也就是第一个xref 的位置
        start_pos = self.getStartxrefPos()
        
        if ( start_pos < 0 ):  # 容错处理
            return -1
        
        posmap["curpos"] = start_pos
        self.xref["retcode"] = -1
        self.xref = self.getxref( posmap, trailer )
        print( sorted( self.xref.items(), key=lambda d:d[0]) ) # 按键值进行排序
        # 删除 偏移量是0的xref 项, 这些都是垃圾项, 没用
        for k,v in sorted( self.xref.items(), key=lambda d:d[0]):
            if (v==0 and k != 'retcode'):
                del( self.xref[k] )                
        
        print("整理后的xref--------------------------------")
        print( sorted( self.xref.items(), key=lambda d:d[0]) ) # 按键值进行排序
        
        if ( self.xref["retcode"] < 0 ):   # 容错处理
            print( "??? 出错了？")
            return -1
        
        print( trailer )
        
        # 获取最原始的页面对象信息. Root 对应的pages 中的页面信息.
        self.getPages( trailer["Root"] )
        
        if ( len(self.pages) <= 0 ):         # 容错处理
            return -1
        
        print( sorted( self.pages.items(), key=lambda d:d[0]) )
        '''
        /*
         * 测试代码， 打印pages 的内容 以及 xref 对象的描述内容
         */
        
        '''
        with open("F:/F_t_tmp/tmp1/Rowpages.txt","w") as fs:
            for k,v in sorted( self.pages.items(), key=lambda d:d[0]): 
                buf =  self.getObjContent( v )
                fs.write( v + "|" + buf + "\r\n\r\n" ) 

        with open("F:/F_t_tmp/tmp1/xrefAll.txt","w") as fs:
            fs.write("len(self.xref) = %d\r\n" % len(self.xref) )
            for key in sorted(self.xref.keys()):
                if ( key != "retcode"):
                    buf =  self.getObjContent( key )
                    #print(key)
                    #print(type(key))
                    fs.write( key + "(%d[%08x])||" % (self.xref[key],self.xref[key]) + buf + "\r\n\r\n" ) 
        '''
        
        // 1. 分析pages 的对象内容(这个哈希表中的对象全部是叶子对象), 如果有Type0则存放在
        // cmaplist 哈希表中    页号:cmap对象1  cmap对象2...,   例如: "1":"5 9"
        // 注意: cmaplist 的第一项是所有cmap对象的汇总, 如: "total":"5 9 27"
        
        
        // 2. 通过cmaplist, 处理total中的每一个cmap对象, 将获取的映射表存放在cmaps哈希表中
        // 内容如下:   "5":cmap 哈希表，  注意: value 是一个哈希表， 存放的是映射内容。
        //     类似:"0528":2382,  注意映射表中的值是 数字, 是为了方便后续处理. 
        // 3. 1与2  放在一个方法里实现
        // cmaplist 的key值 是页面对应的叶子页面的对象编号, 不是页号, 对应的是pages哈希表中的value
        # 2016.12.23:
        #      修改cmaplist 的结构, 需要添加字体名称, 用于解码, 因为有不同type0的字体会出现: 相同编码, 不同解码. 例如. 0779 在C2_0是5149(华), 在C2_1是5143(元)
        #      cmaplist = {页对象编号:{"字体名称":对象编号,"":对象编号}}, 例如:
        #      cmaplist = {"3":{"C2_0":"8", "C2_1":"13"}}
        '''
        cmaplist, cmaps, contentMap ={}, {}, {}
        self.getCmapList( cmaplist, contentMap) 
        
        
        
        # log.info xref 
        print( "========= xref size ====%d" % len(self.xref) )
        print( "========= pages size ====%d" % len(self.pages) )
        print(self.pages)
        print( "========= cmaplist size ====%d" % len(cmaplist) )
        print( "========= cmaplist ====")
        print( sorted(cmaplist.items(),key=lambda d:d[0]) )
        print( "========= contentMap ====%d" % len(contentMap) )
        print( sorted(contentMap.items(),key=lambda d:d[0]) )

        
        self.getCMAPs( cmaplist, cmaps )

        #print(cmaps)

        
        #pageno = "3"
        with open(self.tmpfile1, "w") as fs:
            fs.write("------第%s页测试--------------\r\n" % pageno )
            
        self.processPage( pageno, cmaps, cmaplist, contentMap, "F:/F_t_tmp/tmp1/"+pageno + "_content.txt")
        

    '''
     * 2. getStartxrefPos()
     *      获取startxref 的值， 也就是第一个xref 的物理位置
     *  入口参数:
     *      无
     *  出口参数:
     *      无
     *  返回值:
     *      -1    文件格式错误
     *      >0    startxref 的物理位置
    '''
    def getStartxrefPos( self ):
        try:
            self.file_tools.seek( self.file_tools.getFileLength() - 48 )  #参数为要定位的文件的字符位置，0代表定位在文件的开头

            while(True): #逐行读取该文件，如果定位到文件中一行的中间，则只读取从定位的位置开始的后半部分
                temp = self.file_tools.readLine()
                
                if ( not temp ):   # is null 不行, ！= null 也不行
                    return -1
                
                if ( "startxref" in temp.decode("utf-8") ):  # 表示找到了startxref
                    #print("找到了！")
                    temp = self.file_tools.readLine()      # startxref 的下一行包含位置信息
                    #print( temp )
                    startxrefpos = int( temp )
                    
                    return startxrefpos
            
        except:
            print( "getStartxrefPos() Exception error!")
            traceback.print_exc()
            return -1

    '''
     * getxref()
     *     入口参数:
     *          posmap  (xref位置,一个哈希表，取pos["curpos"]), self.xref, trailer
     *     出口参数:
     *          trailer, self.xref
     *     返回值: 
     *          无
     *              
     *      2016.05.06    重新实现交叉引用表的获取。 处理PDF 1.4 版本的一些文件时发现,
     *       1. xref 的完整构成是   xref + trailer.  如果有多个xref, 那么就有多个trailer.
     *          从最后的trailer 后面的startxref 来获取第一个xref, 然后获得最初的交叉引用表
     *          信息， 然后是一个对应的trailer, 处理这个trailer, 如果有prev, 那么继续下一个
     *          xref 的定位并处理， 然后获得对应的trailer, 再判断是否有prev, 一次类推， 直到
     *          最后一个trailer 没有prev, 表示处理结束.  需要注意的是， 最后的交叉引用表中的
     *          对象的位置信息覆盖之前的self.xref 中的对象的位置信息。
     *       2. 需要注意的是, xref 中的交叉引用表信息处理要注意， 可能会是多个映射关系，比如
     *          
                    xref\r\n        (1373003 所指的位置)
                    0 1\r\n
                    0000000000 65535 f\r\n
                    5267 1\r\n
                    0001368810 00000 n\r\n
                    5569 1\r\n
                    0001372739 00000 n\r\n
                    trailer\r\n
                    <<Size 5570/Root 5270 0 R/Info 5569 0 R/ID[<...><...>]/Prev 1368513>>\r\n
                    startxref\r\n
                    1373003\r\n
                    %%EOF\r\n

     *           这个例子可以清晰看出， 有多个映射关系. 
     *           处理过程如下:
     *           1. 获取startxref 的数据，并定位
     *           2. 判断是否是xref, 如果不是则返回空(也就是出错了)
     *              下面的处理是一个嵌套处理. 
     *               
     *                说明: pos 之所以用哈希表， 是为了容错处理， 如果有些pdf被病毒修改, trailer 的
     *               prev 是互相一样的， 那么会造成处理self.xref 死循环。 这儿要判断后续新的xref 位置是否
     *               已经被处理过了, 如果被处理的话, 也就是在pos 中应该有对应的值， 那么就说明文件出错了，
     *               直接退出不再处理. 
     *               
     *               getxref( pos, trailer )
     *           3. while ( buf = readline() 不包含 trailer ) { // 不包含trailer 也就是没有结尾
     *                  // 循环处理, 确认所有的对象信息都处理到了
     *              }
     *              // 下面处理trailer
     *              trailer["Root"], trailer["Prev"]...
     *              if ( trailer["Prev"] 有效值 ) {
     *                  self.xref += getxref( pos, trailer )
     *                  // 注意， 这儿传入trailer， 那么最后处理的trailer 会覆盖前面处理的trailer 的元素内容. 
     *              }
     *              
     *              return self.xref
     *           4. retcode 错误代码说明: (只有等于0的时候self.xref才是正确的)
     *                  -40421      xref 的位置信息有误， 可能文件已经被破坏
     *                  -40422      xref 格式有误， 可能不是以xref开头
     *                  -40423      xref 格式有误,  第二行不是 起始对象编号 对象数量
     *                  -40431      xref 格式有误,  traile格式有误
     *           5. 注意， 这是个嵌套函数， 如果定义了返回值， 最后一定不要忘记返回xref. 
     *              否则groovy 并不会提示错误， 但是到最后由于没有返回， 调用的时候如果用了赋值， 可能会赋值null
     * depends on:
     *      1. getTrailer()
     *      2. file_tools.readLine()
    '''
    def getxref( self, posmap, trailer ):
        buf = ''
        self.xref["retcode"] = -1
        # 如果posmap["curpos"] 已经处理过, 即在后面的元素中已经有值了，则说明文件被破坏了, 会造成死循环
        
        tmpmap = posmap.copy()
        # tmpmap 是个临时字典, 只在下面一句有用. 用来判断posmap 除了curpos 外, 有没有重复的地址. 直接赋值的话, 修改tmpmap等同于修改posmap
        if ( "curpos" in tmpmap.keys() ):
            del(tmpmap["curpos"])     # 删除这个是为了避免下面的判断出错, 因为这个key一直存在.

        # 下面的判断是为了避免循环处理xref, 也就是已经处理过的xref不再处理, 仅仅是容错处理, 极少有这种情况发生, 就怕错误文件可能会发生
        if ( "curpos" not in posmap.keys() or posmap["curpos"] in tmpmap.values() ) :
            print( "posmap错了1？" )
            return self.xref
        
        # 将当前的posmap["curpos"] 添加到posmap哈希表中, key 和  value 一致。 主要是value, 用来记录处理过的xref位置
        posmap[ posmap["curpos"] ] = posmap["curpos"]
        
        cpos = -1      # 用来记录xref 第一个对象信息的位置, 所有对象的位置信息可以通过计算过的

        try:
            self.file_tools.seek( posmap["curpos"] )
            # 第一行
            buf = self.file_tools.readLine()
            print(buf)
            if ( not buf or "xref" not in buf.decode("utf-8") ): # 如果没有第一行或者第一行不是xref ，格式出错
                self.xref["retcode"] = -40421
                print( "第一行错了？" + buf.decode("utf-8") )
                return self.xref
            
            # 循环处理第二行和后续的， 如果后续的trailer 里面有prev, 则需要嵌套调用getxref()
            while ( True ):
                buf = self.file_tools.readLine()
                if ( not buf ):
                    break

                # 如果是trailer ()  则跳出循环， 直接处理trailer, 如果没有trailer , 后续的判断会出错， 返回-40423错误
                buf = buf.decode("utf-8")
                #buf = str(buf)
                if ( "trailer" in buf   ):
                    print("发现trailer："+ buf)
                    break  
                
                tmp = buf.split(" ")
                if ( len(tmp) != 2 ):     # 如果不是5267 1 之类的格式(起始对象编号 对象数量), 格式出错
                    self.xref["retcode"] = -40422
                    return self.xref
                
                firstObj    = int( tmp[0] )    # 起始对象编号
                objSum      = int( tmp[1] )    # 对象数量

                if ( objSum < 1 ):       # 这种情况几乎不可能， 这儿是为了容错
                    self.xref["retcode"] = -40424       # 尽量用xref["retcode"], 这儿用这种方式， 是为了演示一种访问方式
                    # 2016.12.29: 这种情况有可能, doc文件转存pdf后, 第一个xref 就是0 0, 后面的trailer指向新的xref
                    # 这儿应该继续处理trailer， 如果没有Prev 就错了
                    buf = self.file_tools.readLine().decode("utf-8")   # 获取的应该是 0000000016 00000 n类似格式
                    if ( "trailer" not in buf ):  # 无效的xref之后没有trailer 的话就是格式出错了
                        return self.xref
                    if ("Root" not in buf):# 如果trailer.<<...>>格式的话, trailer的内容实际上在下一行
                        buf = self.file_tools.readLine().decode("utf-8")
                    trailer = self.getTrailer( buf, trailer )
                    if ( trailer["retcode"] < 0 or "Prev" not in buf ):  # 无效的xref之后的trailer无效或没有包含有效的self.xref 地址, 则出错返回
                        return self.xref
                    if ( trailer["Prev"] ) : 
                        print( "嵌套调用前: Trailer：" )
                        print( trailer )
                        posmap["curpos"] = trailer["Prev"]
                        self.xref = self.getxref( posmap, trailer )   # 不用返回值也可以
                        return self.xref
                    else:  # 如果trailer 中没有有效的Prev 也出错
                        return self.xref
                
                cpos = self.file_tools.getPosition()
                for i in range(0, objSum) :
                    self.file_tools.seek( cpos + i * 20 )
                    buf = self.file_tools.readLine().decode("utf-8")   # 获取的应该是 0000000016 00000 n类似格式
                    tmp = buf.split(" ")           #
                    self.xref[ str(firstObj+i) ] = int( tmp[0] )    # tmp 的第一个元素就是obj在文件中的实际位置 
                
                # 处理完一个后， 如果有多个映射描述, 则继续while()大循环处理
                
            self.xref["retcode"] = 0

            # 这儿处理trailer, 如果有Prev, 则需要嵌套调用 getxref(), 根据前面的处理,
            #  下一行读到的就是traier的内容
            if ( "Root" not in buf ):  # 如果trailer.<<...>>格式的话, trailer的内容实际上在下一行
                buf = self.file_tools.readLine().decode("utf-8")
                print("buf="+buf)

            trailer = self.getTrailer( buf, trailer )
            print(trailer)

            if ( "Prev" not in buf ):
                # 如果trailer 不包含 Prev项，表示这是最后一个xref了
                print("已经处理完了最后一个xref")
                return self.xref

            if ( trailer["retcode"] < 0 ) :
                print("trailer 错了？" )
                print(trailer)
                self.xref["retcode"] = -40431
                return self.xref 
            
            if ( trailer["Prev"] ) : 
                print( "嵌套调用前: Trailer：" )
                print( trailer )
                posmap["curpos"] = trailer["Prev"]
                self.xref = self.getxref( posmap, trailer )   # 不用返回值也可以
            
            
            print( "最后" )
            print( self.xref )

            #trailer = trailerBAK.copy()   #
            print("==end==")
            print(trailer)
            
            return self.xref         # 这一句千万不要忘了， 否则groovy 不会提示错误
        except:
            print( "getself.xref() Exception Error" )
            return self.xref
    
        

    '''
     * 4. getTrailer()
     * 2016.05.07
     *    由于xref 的处理方式发生变化, 原来的处理方式有缺陷, trailer 只是xref的一部分
     *       -40411    文件格式非法， trailer 格式错误, 没有找到startxref信息
     *       -40412    文件格式非法， trailer 格式错误, 没有找到trailer信息
     *    1. 处理Trailer, 
               <</Size 51387/Root 1 0 R/Info 50568 0 R/ID[<BE239411BFD7D4D9318C29408037556>
               <5CA7DFC3C76C2F42985CAE05DBD580F9>]/Prev 3275241/xrefStm 771024>>\r\n
     *      获取  Size, Root, Info, ID, Prev, xrefStm  6项 数据. 存放在 哈希表trailer 中的同名key的value 中
     *  入口参数:
     *      trailer 原始字符串
     *  出口参数:
     *      trailer 哈希表
     *  返回值:
     *      trailer 哈希表
     * 调用的外部方法有:
     *      1. -
     *      2. 
     * 调用的类对象内部的方法有:
     *      1. 
    '''
    def getTrailer( self, buf, trailer ):
        
        try:
            trailer["retcode"] = -1         # 初始化为-1, 假设不能获取trailer 成功
            temp = buf[0:len(buf)-2]        # 过滤掉尾部的>>符号， 避免处理出错
            items = temp.split("/")
            flag = False                    # 临时标识， 用来表示是否有Prev 项

            #print(temp)
            #print(items)
            # 以下的解析方法 不采用， 是为了防止出现顺序变化后，需要更新代码， 提高兼容性
            # 因为有些项目是可选的， 比如 Info, ID
            #def keys =["1":"Size","2":"Root","3":"Info","4":"ID", "5":"Prev","6":"self.xrefStm"]
            for item in items :          #   用这个是为了可读性更好点
                # 这儿逐个判断是否是目标item, 实际上是增加了容错功能, 即顺序无关了
                if ( "Size" in item ):      # Size 项
                    trailer["Size"] = int( item.split(" ")[1] )
                
                elif ( "Root" in item ):
                    # Root 项 , 没有解析成list，因为只需要根元素的对象编号即可，整数型字符串
                    trailer["Root"] = item.split(" ")[1] 
                
                elif ( "Info" in item ):
                    # Info 项, 没有解析成list，同样因为只需要对象编号
                    trailer["Info"] = int( item.split(" ")[1] )
                
                elif (  "ID" in item ):
                    # ID 项， 没有解析成list，暂时不处理ID
                    trailer["ID"] = item[3:len(item)-1]
                
                elif ( "Prev" in item ):    # Prev 项
                    trailer["Prev"] = int( item.split(" ")[1] )
                    flag = True
                
                elif ( "xrefStm" in item ):   # xrefStm 项
                    print("-=-================"+item)
                    trailer["xrefStm"] = item.split(" ")[1]
                
            if ( not flag and "Prev" in trailer.keys() ):       # 如果该trailer,没有Prev, 则删除Prev项， 防止沿用之前的内容.
                del( trailer["Prev"] )
            
            trailer["retcode"] = len(trailer)     # 这儿的返回值是获得的有效项目的数量(包括retcode本身)
            
            print( trailer )
            print( "trailer.retcode=%d" % trailer["retcode"] )
            
        except:
            print("getTrailer() Exception Error!")
            traceback.print_exc()
        
        return trailer
    
    '''
     *  5. getPages() 
     *       获取所有的页 对应的对象的信息， 使用内存映射文件来进行操作, 实际上是调用的
     *       getObjContent()方法是用的内存映射文件来访问的.
     *       Root 对象的内容例子如下:  (注意， 下面的例子实际上是没有换行的， 这儿为了方便阅读分行了)
     *       1 0 obj

<</AcroForm 51135 0 R/Lang(zh-CN)/MarkInfo<</Marked true>>
/Metadata 51137 0 R/OCProperties<</D<</AS[<</Category[/View]/Event/View/OCGs[50601 0 R]>>
<</Category[/Print]/Event/Print/OCGs[50601 0 R]>>
<</Category[/Export]/Event/Export/OCGs[50601 0 R]>>]
/ON[50601 0 R]/Order[]/RBGroups[]>>/OCGs[50601 0 R]>>
/Outlines 607 0 R/Pages 2 0 R/StructTreeRoot 1066 0 R/Type/Catalog>>
     *          
     *          通过上面的Root信息, 可以获得pages 对象信息， 然后通过这个对象编号在获得
     *          所有的页面对应的原始对象的编号(该对象未必是内容对象，即不是叶子对象)
     *          (下面的例子中Kids中的内容省略了很多， 不然太长)
     *          
     *          Pages 对象含有Kids 项, 该项包含的就是页面对象。 该页面对象有可能还会含有Kids项.  
     *          只有含有content的对象才是叶子对象， 否则都应该含有Kids项。 
     *          
2 0 obj
<</Count 266/Kids[3 0 R。。。298 0 R 299 0 R]/Type/Pages>>
     *
     *          另外: 含有Content的叶子对象， 可能有多个stream 对象。 即一页对应多个内容对象。如下:
     *          5272||<</Contents[5278 0 R 5279 0 R 5280 0 R 5281 0 R 5282 0 R 5283 0 R 5291 0 R 5292 0 R]/CropBox[9 0 603 792]/MediaBox[0 0 612 792]/Parent 5252 0 R/Resources 5273 0 R/Rotate 0/Type/Page>>
     *          参见:
     *              page信息.txt    --- 一个英文PDF文件的Root, Pages, Kids, Content 对象的信息罗列。
                注意: 
                    如果是全英文pdf 文件， 可能没有type0 对象, 也就是没有cmap 对象列表
     **
     *  入口参数:
     *          root    是 Root 对象编号, 字符串
     *          self.xref    哈希表， 存放的是所有对象的物理位置信息
     *  出口参数:
     *          pages   哈希表, 存放的是 原始页面对应的叶子对象编号(字符串)
     *                  
     *          
     *  返回值:
     *          pages 哈希表, 内容 与 出口参数 一致
     * 调用的外部方法有:
     *      1. 
     * 调用的类对象内部的方法有:
     *      1. getObjContent(0
     *      2. getPageLef()
    '''
    def getPages( self, root ) :
        
        try :
            print("====1=====getPages(), root="+ root)
            print(type(root))
            # 获取 Root 对象的信息
            tmp = self.getObjContent( root )
            print(tmp)
            print( "root("+root+")位置: "+ str(self.xref[root]) +"| 内容:" + tmp )
            
            obj = ''         # 字符型
            # 获取Pages 对象的编号
            items = tmp.split("/")
            for item in items :
                if ( "Pages" in item ):     # 表示找到了包含Pages 的项目
                    obj = item.split(" ")[1]        # Pages 对应的对象编号
                    break
                
            print( "getPageleaf()前 len(pages)=%d Pages=%s" % (len(self.pages),obj ))
            self.getPageleaf( obj )
            print( "getPageleaf()后 len(pages)=%d" % len(self.pages) )
            return 0
            
        except:
            print("getPages() Exception Error.")
            return -1
        
    
        
    '''
     * 6. getObjContent()  
     *      根据对象编号获取对象的内容, 使用内存映射文件 
     * 入口参数:
     *      obj     是整数字符串 ， 对应的是对象编号
     *      self.xref    self.xref哈希表， 存放的是 对象编号:对象物理位置
     * 返回:
     *      对象的文字描述内容部分.
     * 说明:
     *      对象的描述部分， 第一行是 3 0 R , 也就是对象编号等信息, 直接过滤即可. 
     *      第二行才是对象的描述性文本内容.
     * 2016.12.19:
     *      修正, 对于有 \xae 类似的内容, 需要额外处理.
     * 调用的外部方法有:
     *      1. seek() ------------------>util_fileService
     *      2. readLine() -------------->util_fileService
     * 调用的类对象内部的方法有:
     *      1. getObjPosInself.xref()
    '''
    def getObjContent( self, obj ):
        content = ""
        try:
            if ( len(self.xref) == 0 ):
                return content
            #print("getObjContent(). self.xref, obj="+obj)
            #if ( obj == '30'):
            #    print("30对象的位置%d" % self.xref[obj])
            self.file_tools.seek( self.xref[obj] )
            buf = self.file_tools.readLine()
            #print("第一行=%s" % buf)
            buf = self.file_tools.readLine()
            #print("第二行=%s" % buf)
            # 这儿不得已增加了一个容错机制, 会很大的影响效率, 因为有些文档读出来的字节流中, 有\xae 类似的字节, 无法utf-8解码
            # 不用解码, 直接转换为str即可. 解码在解压数据流的时候再用
            #j = 0
            #for i in range( 0, len(buf) ):
            #    if ():
            content = str(buf)                     #.decode("utf-8")
            #print("content=%s" % content)
            #content = self.file_tools.readLine().decode("utf-8")
        except:
            print( "getObjContent() Exception Error!" )
            traceback.print_exc()
        
        return content


    '''
     * 7. getPageleaf() 
     *      获取页号对应的内容对象, 结果存放在pageLeafs哈希表中
     *      附加功能是同时将该内容对象使用的cmap也获取后存放在cmaplist哈希表中(英文文件没有type0字体，也就是没有cmap)
     * 入口参数:
     *      pageObj     页对象编号字符串, 例如 "3"
     *      self.xref        交叉引用表, 哈希表, 用来检索对象的物理位置
     * 出口参数:
     *      pageleaf    存放 页号: 内容对象编号 的哈希表
     *      cmaplist    存放 页号: cmap 对象编号 的哈希表, 需要注意的是， 第一个item 是 total : 所有的cmap对象编号
     * 返回值:
     *      0      正确
     *      <0     错误
     * 说明:
     *      1. 循环处理pages 的页面对象, 
     *         需要注意的是做避免死循环的容错处理。 记录当前页面寻找内容对象过程中处理过的
     *         对象编号, 如果该对象编号已经被处理过， 又出现, 说明文件已经被破坏, 返回-1 退出.
     *      2. 只要有Kids 那么就继续往下检索， 直到没有Kids 项， 那么就是叶子对象
     *          例如:
     *              5251||<</Count 100/Kids[5252 0 R 5253 0 R 5254 0 R 5255 0 R 5256 0 R 5257 0 R 5258 0 R 5259 0 R 5260 0 R 5261 0 R]/Parent 5250 0 R/Type/Pages>>
     *              
     *      3. 叶子对象都会有个Contents 项， 参见Page信息.txt
     *          例如:
     *              5272||<</Contents[5278 0 R 5279 0 R 5280 0 R 5281 0 R 5282 0 R 5283 0 R 5291 0 R 5292 0 R]/CropBox[9 0 603 792]/MediaBox[0 0 612 792]/Parent 5252 0 R/Resources 5273 0 R/Rotate 0/Type/Page>>
     *               注意: Contents 的内容有可能是多个stream 对象
     *               如果有type0的话, 就定义在这儿， 也就是有Contents 的对象中
     *       4. 这个方法也是用嵌套调用
     *       
     *       5. 2016.05.11   注意, Kids 前面的Count 是所有的该对象的叶子对象数量， 而不是后面的Kids的数量。
     *          也许后面的Kids 中的对象还有子对象。
     *           
     * 
    '''
    def getPageleaf( self, pageObj ):
        try:
            retcode = -1
            
            #获取指定的页对象的描述信息， 例如:
            # 5251||<</Count 100/Kids[5252 0 R 5253 0 R 5254 0 R 5255 0 R 5256 0 R 5257 0 R 5258 0 R 5259 0 R 5260 0 R 5261 0 R]/Parent 5250 0 R/Type/Pages>>
            buf = self.getObjContent( pageObj )
            #print( "1.buf=" + buf )
            if ( "Kids" in buf ):
                tmp = buf.split("/") 
                kidscount, kidStr = 0, ''
                for item in tmp:
                    if ( "Count" in item ):
                        kidscount = int( item.split(" ")[1] )        # buf[0] = "<<", 所以跳过
                    
                    elif ( "Kids" in item ):
                        p1, p2 = item.index('['), item.index(']')
                        kidsStr = item[p1+1:p2].strip()         # 获取[] 中的内容

                
                items = kidsStr.split(" ")
                #print("kidsStr="+kidsStr)
                length = len(items)
                for i in range(0, length // 3 ): # 不能用kidsCount 否则会数组溢出
                    obj = items[ i * 3 ]          # 对象编号
                    if ( list(self.pages.values()).count( obj ) >=1  ):  # dict.values() 本身不是list， 而是dict_values, 需要转换为list类型
                        print( "该叶子被重复使用了(under "+ pageObj + "),leaf=" + obj )
                        print( self.pages )
                        return -1
                    self.getPageleaf( obj )
                
            elif ( "Contents" in buf ):    # 只有含有 Contents 的对象才是真正的叶子对象
                #print("=====|||"+buf+":pageObj="+pageObj)
                if (  list(self.pages.values()).count( pageObj ) >=1  ):  # 如果已经处理过, 就不再处理.
                    print( "pageleaf已经有了" + pageObj )
                    return -1
                   
                #print( "|| 这是一个叶子:" + pageObj )
                self.pages[ str( len(self.pages)+1 ) ] = pageObj
                #print( sorted( pageleaf.items(), key=lambda d:d[0]) )
            
            return 0

        except:
            print( "getPageleaf() Exception Error"  )
            traceback.print_exc()
            return -1
        
        
        return 0
    
    '''
     * 8. getCmapList()
     * 
     * 入口参数:
     *      pages
     *      self.xref
     * 出口参数:
     *      cmaplist
     *      cmaps
     * 返回值:
     *      无
     *  1. 分析pages 的对象内容(这个哈希表中的对象全部是叶子对象), 如果有Type0则存放在
     *  cmaplist 哈希表中    页号:cmap对象1  cmap对象2...,   例如: "1":"5 9"
     *  注意: cmaplist 的第一项是所有cmap对象的汇总, 如: "total":"5 9 27 " (后面多了一个空格, 不影响处理)
     *
     *
     *  2. 通过cmaplist, 处理total中的每一个cmap对象, 将获取的映射表存放在cmaps哈希表中
     *  内容如下:   "5":cmap 哈希表，  注意: value 是一个哈希表， 存放的是映射内容。
     *      类似:"0528":2382,  注意映射表中的值是 数字, 是为了方便后续处理. 
     *  3.  第2项单独方法实现  getCmaps()
     *  
     *  4. 同时把 页面内容对应的对象编号(可能是多个) 也获取了, 存放在哈希表里 ContentMap
     *  
     *  5. 例子:
     *      3|<</Contents 51134 0 R/Group<</CS/DeviceRGB/S/Transparency/Type/Group>>/MediaBox[0 0 595.32 841.92]/Parent 2 0 R/Resources<</ExtGState<</GS0 50603 0 R>>/Font<</C2_0 5 0 R/TT0 10 0 R/TT1 12 0 R/TT2 14 0 R/TT3 17 0 R>>/ProcSet[/PDF/Text/ImageC]/XObject<</Fm0 50597 0 R/Im0 16 0 R>>>>/StructParents 0/Tabs/S/Type/Page>>
     *      
     *      5272|<</Contents[5278 0 R 5279 0 R 5280 0 R 5281 0 R 5282 0 R 5283 0 R 5291 0 R 5292 0 R]/CropBox[9 0 603 792]/MediaBox[0 0 612 792]/Parent 5252 0 R/Resources 5273 0 R/Rotate 0/Type/Page>>
     * 2016.12.23:
     *      修改实现方式, cmaplist ={pageno:{"type0obj":type0Name}}
     #      total 仍然保留, 主要是为了解析cmaps是用。 不过存储方式由字符串改为列表, 列表的元素也是dict, {"FontObj":"FontName"}
     * 2017.01.09:
     *      有时候会发生某个cmap没有解析出来的情况. 比如如果对应3个cmap, 有一个就没有。
     * Depends ON:
     *      self.isType0()
    '''
    def getCmapList( self, cmaplist, contentMap):
        try:
            cmaplist["total"] = {}      # cmaplist 哈希表的total 项是所有cmap对象的汇总， 便于后续处理获得CMAP
            print("getCmapList()----------------------------------------------begin")
            for key,v in sorted( self.pages.items(), key=lambda d:d[0]):
                buf = self.getObjContent( v ).strip()
                print("pages[%s]=%s(obj=%s)," % (buf,key,v) )
                buf = buf[ 2: len(buf) - 2 ]        # 过滤前后的<< >>
                tmp = buf.split("/")
                for i in range( 0, len(tmp) ):
                    print(tmp[i])
                    if ( "Contents" in tmp[i] ):
                        #println tmp[i]
                        if ( "[" in tmp[i] ):        # 如果有中括号, 说明该页对应的内容对象可能是多个
                            p1, p2 = tmp[i].index('['),  tmp[i].index(']')    # 获取'[' , ']' 的位置
                            buf = tmp[i][ p1+1 : p2 ].strip()     # 取方括号中的内容
                            s = buf.split(' ')
                            tmp1 = ""
                            for j in range(0, len(s) ):
                                if ( i % 3 == 0 ):     # 只取对象编号
                                    tmp1 += s[i] + " "
                            # 删除尾部多余的空格
                            contentMap[ self.pages[key] ] = tmp1.strip()
                        else:
                            contentMap[ self.pages[key] ] = tmp[i].split(" ")[1]    # 类似 Contents 101 0 R
                        
                    '''
                    // 下面处理type0 的对象, 也就是cmap对象
                    // 1. 先获取 叶子对象的信息中的Font内容
                    // 2. 解析 Font 内容， 获得各个字体对象的对象编号
                    // 3. 处理字体对象(依据获得的对象编号获得内容), 如果该对象内容有Type0, 表示是cmap, 处理记录
                    // /Font<</C2_0 5 0 R/TT0 10 0 R/TT1 12 0 R/TT2 14 0 R/TT3 17 0 R>>
                    // Font 部分是后面<<>>包含字体内容， 但是字体又都是/开始的，
                    '''
                    if ( "Font" in tmp[i] ) :
                        #println "字体？" + tmp[i]
                        cmap = {}       # 存放Type0 的信息{ "字体名称":对象编号,}
                        i += 1      # Font 的下一项及后面的, 就是对象编号 比如 C2_0 5 0 R , TT0 10 0 R等
                        while ( i < len(tmp) ):
                            #println "具体字体:" + tmp[i] + "|" + tmp[i].split(" ")[1] + "|"
                            fontName    = tmp[i].split(" ")[0]
                            obj         =  tmp[i].split(" ")[1]     # C2_0 5 0 R 拆分后, 第二个元素就是对象编号
                            if ( self.isType0( obj ) ) :   # 判断是否是Type0 字体
                                cmap[ obj ] = fontName
                                
                                if ( obj not in cmaplist["total"].keys() ):  # 如果没有在total 项中登记, 则添加 
                                    cmaplist["total"][obj] = fontName
                                
                            if ( ">>" in tmp[i] ) :   # 最后一个字体，字体结束, 跳出本循环
                                break
                            
                            i += 1
                        # 删除尾部多余的空格
                        cmaplist[ self.pages[key] ] = cmap.copy()
                    
        except:
            print( "getCmapList() Exception Error:" )
            traceback.print_exc()

    '''
    /*
     * 10. getCMAPs()
     *      获取所有的CMAP对象额编解码信息，并存放在哈希表中.  "对象编号":编解码映射哈希表
     * 入口参数:
     *      cmaplist
     *      self.xref
     * 出口参数:
     *      cmaps
     * 2016.12.23:
     *     1. cmaplist修改为: {"pageobj":{"fontobj":"fontobj"}, "total":[{},{}]}, 相应的cmaps
     *     2. cmaplist 的 total 修改为列表了, 所以实现方式也进行修改.
     * depends on:
     *      self.getObjContent()
     *      self.getItemOfObj()
     *      self.procType0Stream()
     */
    '''
    def getCMAPs( self, cmaplist, cmaps ):
        try:
            # 如果cmaplist["total"]里面没有对象编号, 说明没有中文等需要编解码的内容,不需要cmap, 直接返回
            print( 'begin of getCMAPs() ')
            if ( len( cmaplist["total"] ) == 0 ) :      
                return 
                
            print( '---------- getCMAPs()  total:---------------' )
            print( cmaplist["total"] )
            for obj,fontname in sorted(cmaplist["total"].items(), key=lambda d:d[0]) :           # 是个dict, 每一项是 "对象编号":"字体名称", 例如: "8":"C2_0"
                print( "obj=%s, fontname=%s" % (obj, fontname) )
                # 5||<</BaseFont/ABCDEE+#CB#CE#CC#E5/DescendantFonts 6 0 R/Encoding/Identity-H/Subtype/Type0/ToUnicode 50569 0 
                content = self.getObjContent( obj )      # 获取cmap 对象的描述信息
                print("内容对象(%s)(%d)的描述: %s" % ( obj, self.xref[obj], content ) )
                if ( "ToUnicode" not in content ) :        # 如果该cmap 信息不包含"ToUnicode"
                    print( "CMAP:" + obj + ":Error 1, no ToUnicode" )
                    print(content)
                    return                            # 继续处理后面的CMAP
                content = self.getItemOfObj( obj, "ToUnicode" )      # 存放 对象的描述信息
                if ( content == "" ) :                #说明没有找到ToUnicode项， 出错了
                    print( "CMAP:" + obj + ":Error 2, no ToUnicode" + "content=:"+ content )
                    return                            # 继续处理后面的CMAP
                
                # 获取CMAP stream 对象编号
                tmpobj = content.split(" ")[1]      # ToUnicode 50569 0 
                #print( content )
                #print( tmpobj )
                #cmap = {}
                cmap = self.procType0Stream( tmpobj )  # cmap 是dict 字典
                print( "cmap(" + obj + "):"+tmpobj+"的映射内容为:" )
                #print( cmap )
                cmaps[fontname] = cmap      # 由原来的对象作为key, 修改为 字体名称作为key, 因为后面的解码的时候是要根据字体名称来解码的
            
            print( "所有的映射内容为：" )
            #print( cmaps )
            print( 'next of getCMAPs() %s' % cmaplist["total"] )
        except:
            print( "getCMAPs() Exception Error:" )
            traceback.print_exc()

    

    '''
    /*
     * 9. isType0()
     *      判断指定对象是否是Type0 对象, 也就是CMAP 对象
     * 入口参数:
     *      obj     对象编号字符串
     *      self.xref    交叉引用表, 哈希表， 对象编号(字符串): 对象位置(数字)
     * 出口参数:
     *      无
     * 返回值
     *      true    是 Type0 对象
     *      false   不是 Type0 对象
     */
     '''
    def isType0( self, obj ):
        try:
            buf = self.getObjContent( obj )
            if ( "Type0" in buf ) :     # 如果有Type0 项, 则表明是CMAP
                return True
            else:
                return False
            
        except:
            print( "isType0() Error:" )

    '''
    /*
     * 11. getItemOfObj() 
     *      获取指定对象的描述信息中的指定项
     * 入口参数:
     *      obj         对象编号, 字符串
     *      self.xref        交叉引用表, 哈希表
     *      item        指定项名称, 字符串
     *      splitchars  分隔符， 缺省是"/"
     * 出口参数
     *      无
     * 返回值
     *      ""   失败
     *      非空字符串，也就是指定项的内容
     * 注意：
     *      对于叶子对象的字体信息， 处理方式需要独立, 因为其内容也是"/"分隔。     
     *
     * depends on :
     *      self.getObjContent()
     */
    '''
    def getItemOfObj( self, obj, item, splitchars = "/" ) :
        try:
            objcontent = self.getObjContent( obj )
            print( "obj:" + objcontent + "item="+ item )
            
            if ( "Font" not in item ) :           # 不是Font的处理
                tmp = objcontent.split( splitchars )        # 根据分隔符来拆分对象描述信息
                for i in range(0, len(tmp) ): 
                    if ( item in tmp[i] ):        # 如果包含目标item 则就是需要找的
                        print( "find it :" + tmp[i] )
                        if ( ">>" in tmp[i] ) :    # 如果带有">>", 有可能是最后一项, 过滤掉后面的>>部分
                            tmp[i] = tmp[i].split(">>")[0]
                        
                        return tmp[i]      #  注意， 返回的内容是包含item 项名称本身的
                    
                
            else:
                print( "这个不应该不执行。。。。" )
            
            print( "如果正常， 不应该执行到这儿" + objcontent )
            return ""
        except:
            print( "getItemOfObj() Exception error!" )
            return ""

    # 12. procType0Stream()
    #      获取cmap 的编码
    # 2015.12.25 
    #      使用内存映射文件来实现
    # 2016.12.20
    #      增加了flag参数, 用来确定是否需要再跳过一行. 
    # depends on:
    #     getItemOfObj(), decompress(),
    #     file_tools.read(), .initStreamBuf(), .readLineST()
    def procType0Stream( self, obj ) :
        cmap = {}

        # 1. F052  是里面有对钩的方括号, 无法print(), 也无法在txt文件中显示. 
        codeFilter = ["F052", "F0FE"]
        
        print( "procType0_1()#####对象编号为：" + obj )
        try :
            # 有2种情况.
            # 50569||<</Filter/FlateDecode/Length 7645>>stream
            # 50569||<</Filter/FlateDecode/Length 7645>>\r\nstream

            content = self.getItemOfObj( obj, "Length" ) 
            if ( content == "" ):    #  说明没有找到Length项， 出错了
                print( "CMAP:" + obj + ":Error 3, no ToUnicode Length" )
                return                            # 继续处理后面的CMAP
            
            len1 = int( content.split(" ")[1] )    # 取7645 数字， 也就是字节流长度
            # 下面的处理要小心, 如果上面的content 中包含stream, 就不要再跳过一行了, 如果不包括, 才需要跳过一行。。。！！！！！！
            content = self.getObjContent( obj ) 
            if ( "stream" not in content):    # 2016.12.20  用来区分是\r\nstream\r\n 还是stream\r\n
                print("没有stream, 需要再跳过一行--------------------------")
                buf = self.file_tools.readLine()                        # 跳过 stream\r\n
            buf, len1 = self.file_tools.read( len1 )  # 由于通过 getItemOfObj(), 内存文件 正好定位到stream 的起始位置
            if ( obj == "51134") :
                print( "pos=%d; l=%d; len=%d, stream=" % ( self.file_tools.getPosition(),l, len1 ) )
                print( buf )

            with open("f:/F_t_tmp/tmp1/%s_row.dat" % obj, "wb") as fs:
                fs.write(buf)
                
            
            # OK， 现在 buf 中的字节流就是steam 的内容， 下面进行解压, 解压后的内容存放在desbuf
            desbuf = ''
            desFile =  "f:/F_t_tmp/cmap/"+obj+"_stream.txt"
            print("procType0Stream() 910 ")
            #desbuf = self.decompress( buf.decode("utf-8"), len1, desbuf, desFile )
            print(desbuf)
            desbuf = self.decompress( buf, len1, desbuf, desFile )

            print("procType0Stream() 913 ")
            # 下面处理desbuf, 来获得具体的编码映射关系

            '''
            // 下面开始解析 CMAP
            // 1. 将 CMAP 原始字节流 放置在内存映射中，便于处理
            // 2. 逐行读取 ，然后将字节流转换成字符串
            //    2.1. 如果有 beginbfchar, 则读取前面的数字， 表示是下面几行是几个字符映射， 
            //          也就是循环处理行数的次数， 然后结尾是 endbfchar
            //    2.2 如果有 beginbfrange， 同样读取前面的数字， 表示线面几行是范围映射， 
            //          前面的2个<> 是范围， 后面的<> 是对应实际字符的起始编码。  处理完后 
            //          结尾是 endbfrange
            '''
            
            streambuf = {}
            self.file_tools.initStreamBuf( desbuf , streambuf )

            while ( True ) :
                tmpbuf = self.file_tools.readLineST( streambuf ).decode('utf-8')
                if ( not tmpbuf ):            # 没有数据了
                    break
                if ( "endcmap" in tmpbuf ) :   # 这而增加退出循环的处理， 是为了防止有些缓冲区可能有遗留的"尾巴"
                    print('endcmap 发现了!')
                    break
                
                # 2 beginbfrange
                #    <00B2> <00B2> [<2014>]
                #    <00B3> <00B4> <201C>
                #    endbfrange
                #    这种格式的需要额外处理， 及解码有中括号
                # 还有个begincodespacerange  .... 这个可能是限定编码范围的
                if ( "beginbfchar" in tmpbuf ) :    # 单个编码映射
                    keys = tmpbuf.split(" ")
                    mapsum = int( keys[0] )         # 记录每个段落的映射数量, 获取到这个数据后, keys 就没用了, 所以下面就复用了这个变量名称
                    for i in range( 0, mapsum ) :         # 循环逐个取出编码映射表
                        tmpbuf  = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        keys    = tmpbuf.split(" ")            # 这儿是重复利用keys变量，拆分编码
                        
                        key, value = keys[0][1:5], keys[1][1:5]
                        
                        if ( value in codeFilter ):
                            value = '0020'             # 用空格替代
                        cmap[ key ] = int( value, 16 )
                        
                    
                 # 2016.04.23 
                 #      对于beginbfrange, 序号注意的是， 后面的编码可能是序列或者枚举型
                 #      序列的话， 只有第一个，用尖括号包起来
                 #      枚举型的话， 使用方括号包起来， 里面的每一个尖括号对应的是前面的一个原码
                 #
                if ( "beginbfrange" in tmpbuf ):  # 范围编码映射表
                    keys = tmpbuf.split(" ")
                    mapsum = int(keys[0])      #这儿记录的是范围映射条数, 获取到这个数据后, keys 就没用了, 所以下面就复用了这个变量名称
                    for i in range(0, mapsum) : # 循环逐个取出编码映射表
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        keys = tmpbuf.split(" ")            # 这儿是重复利用keys变量，拆分编码
                        codestart = int( keys[0][1:5], 16 ) # codestart映射的起始位
                        rangelen = int( keys[1][1:5], 16 ) - codestart + 1   #  用来记录范围映射的长度

                        if ( "[" in keys[2] ) : 
                            # 如果有方括号就是枚举型, 那么对keys 数组， 第3个(下标是2)的第一个字符是'[',
                            # 第rangelen+2个的最后一个字符是']' ， 需要过滤
                            keys[2] = keys[2][1:6]    # 第一个，把 开始的'[' 过滤掉

                            # 最后一个由于']'在结尾， 不影响处理， 就不处理了
                            # else if ( j == rangelen -1 ) { // 最后一个，把最后的']'过滤掉
                            #     keys[j] = keys[j]

                            for j in range( 0, rangelen ):
                                key = codestart + j     # 用来处理cmap 的key 与value
                                
                                value = int( keys[2+j][1:5], 16) + j
                                cmap[ str("%04X" % key ) ] = value 
                            
                        else:       # 如果没有方括号，表示是连续性的
                            mapstart = int( keys[2][1:5], 16)   # mapstart编码的起始位
                            for j in range(0, rangelen ):
                                key = codestart + j
                                value = mapstart + j
                                # 2016.04.16          value 不用字符串格式， 直接用16进制值，便于后面解码
                                # 放弃这种方法， 直接用上面的字符串之前 加 \\u 来组建Unicode字符串， 然后转换即可
                                # 这样的话就不用进行字节操作， 不用关心内存的申请了
                                # 2016.04.25  仍然使用数值， 因为解码的时候使用数值更方便
                                cmap[ str("%04X" % key ) ] = value 
                            
        except:
            print( " procType0Stream() 出错了3333 ..." )
            traceback.print_exc()

        return cmap
    


    '''
    /** 
     * 13. decompress()  
     *     解压缩目标字节流
     *  入口参数:
     *  出口参数:
     *  返回值:
     *  
     *  说明:
     *  2015.12.25 :
     *      在方法内部申请一块临时内存， 大概10倍 len 的空间， 保证足够存放加压后的内容.
     *      正式使用 不适用临时文件存放加压内容， 保证性能
     *      其中 desbuf  仅仅是传入的地址， 在本方法内部进行空间申请， 因为解压后的长度在解压前未知
     *  2015.12.26 :
     *      对于传入的字节数组对象参数desbuf , 虽然在 方法内部进行的修改， 但是， 
     *      由于申请空间是在方法内部， 如果不返回该字节数组desbuf 并在方法外给desbuf 赋值, 那么方法外部仍然是null
     *      
     *      这儿有个隐患： 对于这种方式申请的内存， Groovy 不知道释放的彻底不， 如果不行， 就得定期重启系统来释放垃圾内存。
     *
     * depends on:
     *     import zlib,   ---> zlib.decompress()
     */
    '''
    def decompress( self, srcbuf, length, desbuf, desFile ) :
        try:
            #deflate_compress = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)  
            #zlib_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)  
            #gzip_compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)

            #deflate_data = deflate_compress.compress(srcbuf) + deflate_compress.flush()

            #desbuf = zlib.decompress( deflate_data )
            desbuf = zlib.decompress( srcbuf )   
            #desbuf = zlib.decompress( srcbuf, -zlib.MAX_WBITS)   # deflate
            #desbuf = zlib.decompress( srcbuf, zlib.MAX_WBITS|32)      # 自动检测头部
            #desbuf = zlib.decompress( srcbuf, -zlib.MAX_WBITS) 
            with open( desFile, "wb" ) as fs:
                fs.write(desbuf)
            return desbuf
        except:
            print("decompress() Exception Error!")
            traceback.print_exc()
        return ""
      

    '''
    /*
     * 14. processPage()
     *      处理指定页， 获得其内容，存放在指定文件中 (调试过程中需要存放在文件中, 正式使用只需要在内存中)
     * 入口参数
     *     self.pages
     * 出口参数
     * 返回值
     * 实现思路:
     *      1. PageNo 是实际的物理页号, 比如"1" 表示第一页
     *      2. 通过pages[Pageno] 获得对应的叶子对象编号 obj
     *      3. 将obj 对象涉及到的cmap 合并    cmaplist[obj]存放的是它使用的cmap对象编号，
     *           解析后，将cmaps[cmap对象编号] 合并成一个哈希表, 存放在cmap中
     *           注意: cmaplist和 contentMap的 key 值 对应的是pages的value
     *      4. 获取obj 对应的内容对象的编号, contentMap[PageNo]
     *      5. 依次处理内容对象,然后按以下顺序逐一进行处理
     *          5.1 然后获取其stream 字节流(参考 procType0Stream() )
     *          5.2 解压 字节流
     *          5.2 解码 字节流, 存放在目标文件中。
     * depends on:
     *      getItemOfObj()
     */
    '''
    def processPage( self, PageNo, cmaps, cmaplist, contentMap, desFile ):
        try :
            #cmap = {}
            desbuf = ''
            
            buf = cmaplist[self.pages[PageNo]]      # 该页面用到的CMAP, 有可能为空, 即全英文文档
            #print( "第" +PageNo+"页("+self.pages[PageNo]+")--cmap对象有:" + buf + ":" )
            '''
            if ( buf != ""):   # 有cmap
                tmp = buf.split(" ")
                for item in tmp:        # 遍历该页面使用道德所有的cmap, 将其合并为一个哈希表
                    cmap.update( cmaps[item] )    # dict 相加, 如果有重复内容, 由后面的内容替代前面的
            '''    
            # 获取内容对象, 有可能是多个
            buf = contentMap[ self.pages[PageNo] ]
            #print( "第" +PageNo+"页--内容对象有" + buf )
            tmp = buf.split(" ")        # 有可能是多个内容对象
            # 每个内容对象的描述信息类似于(51134的对象描述), <</Filter/FlateDecode/Length 1117>>stream
            for i in range( 0, len(tmp) ): 
                obj = tmp[i]
                buf = self.getItemOfObj( obj, "Length" )        # 获取该内容对象的字节流长度
                if ( buf == "" ) :   # 如果获取长度失败, 说明文件已经被破坏
                    print( "第"+PageNo+"页已经被破坏 (1)" )
                    return

                #print(buf)
                len1 = int( buf.split(" ")[1] )    # 取7645 数字， 也就是字节流长度

                # 下面的flag 判断stream是否在当前对象描述信息中.
                buf = self.getObjContent( obj )
                if ( "stream" not in buf ):
                    self.file_tools.readLine()         # 跳过 stream\r\n 这一行非数据
                buffer, len1 = self.file_tools.read( len1 )    # 由于通过 getItemOfObj(), 内存文件 正好定位到stream 的起始位置, 注意返回的是2个参数
                #print("解压前, 读取的数据:！")
                #print(buffer)
                #print(len1)
                #with open("f:/F_t_Tmp/tmp1/"+obj+".dat","wb") as fs:
                #    fs.write( desbuf )

                # OK， 现在 buffer 中的字节流就是steam 的内容， 下面进行解压, 解压后的内容存放在desbuf
                desfile = "F:/F_t_tmp/tmp1/"+PageNo+"_"+obj+"_stream.txt"
                desbuf = self.decompress( buffer, len1, desbuf, desfile )

                # 如果有cmap, 那么需要对desbuf进行解码, 否则就进行格式调整.
                print("解压结束！")

                '''
                desFile = "e:/t_tmp/page/" +obj + ".dat"

                RandomAccessFile wd = new RandomAccessFile( desFile, "rwd" )
                wd.write( desbuf, 0, desbuf.size() )
                wd.close()
                
                '''
                # 下面开始解码, 无需判断是否cmap 为null 或空， 如果解压后的内容有<>, 必然需要解码
                desFile = "F:/F_t_tmp/tmp1/" +obj + "_decode.dat"
                self.decode( desbuf, cmaps, desFile )
            
        except:
            print( "processPage() Exception Error : " )
            traceback.print_exc()
        

    ###############################################################
    # 下面的方法都是涉及解压后的内容的具体解码以及格式的处理
    #
    #  2016.12.04
    #      从 Groovy 版本移植, 内容处理方面进行了较大的优化, 可读性等得到提高, 处理结果也完善了(主要是换行)
    #      ( Groovy 版本是从Java 版本实现思路移植而来, Java版本由于机器硬盘及备份硬盘损坏, 全部遗失)
    #
    '''
    /*
     * 15. decode()
     *      对给定的字节流进行解码
     * 思路:
     *      1. 将每一部分的处理都模块化
     *      2. 最高一级(I级)是 processBDC, processBT， 所有的处理都在这BDC/EMC, BT/ET 之间， 
     *         这2中之间也会互相嵌套
     *      3. II级 处理是: 
     *          processTD, processTd, processTm, processT*        文本位置
     *          processTJ, processTj, processQuote, processDblQuote         文本显示, 后两个是单引号, 双引号的处理
     *          processTc, processTw, processTz, processTL, processTf,processTr, processTs  文本状态
     *          表格处理？？？
     *      2016.12.08:
     *          采用虚拟纸张的技术来进行内容编排, 即 处理后的数据存放在一个虚拟纸张的内存中，然后输出这个数据即可.
     *          virtual_Page={["Y坐标值": 文字内容],}
     *          然后输出的时候只要对virtual_Page 按照关键字排序后进行输出即可.
     *          坐标处理: 当前坐标如果与已有坐标中的某个坐标相差小于1, 则可视为同一行 。 因为最小的字体也会大于1个像素
     *          {Y:["文字内容","长度", 单位长度]},
     *               单位长度是文字的字体的长度, 用来判断下一文字是否需要与该文字之间有分隔符
     *               如果下一段文字的起始x坐标与该文字的x+len 小于单位长度, 则不需要分隔符.
     *      2016.12.21:
     *          之前的处理, 还是有很多不完善的地方, 主要是没有按照pdf 的环境的设计思路. 下面完善设计思路, 增加 图形状态stack 实现.
     *            用GraphStateStack 记录当前压栈的所有 图形状态, cur_graph_state 用来记录当前的图形状态. 考虑到只处理文本,
     *            图形状态只记录 tm. 
     * depends on:
     *        file_tools.initStreamBuf(), .readLineST( streambuf)
     *        self.processBT(), .processBDC()
     */
    '''
    def decode( self, buf, cmaps, desfile ) :
        try :
            streambuf = {}
            self.file_tools.initStreamBuf( buf , streambuf )
            
            # 字体大小对应的长度, Ps(px):磅(pt), 这个暂时用不上, 但是保留, 也许以后有用
            fontsize = {"5":5.3,    "5.5":5.9,  "6.5":7.0,  "7.5":8.0,  "9":9.6,
                            "10.5":11.2,"12":12.8,  "14":15.0,  "15":16.0,  "16":17.1,
                            "18":19.3,  "22":23.5,  "24": 25.7, "26": 27.8, "36":38.5,
                            "42":44.9}

            print("--decode():camps.keys()")
            print(cmaps.keys())
            retbuf = ""
            cur_xy, cellMap, cellIndexMap, textMap, tm, tf = {}, {-1:{"x":0,"y":0,"w":0,"h":0}}, {}, {}, {}, {}  # 坐标信息, 表格信息(初始化页眉是没有的, -1用于页眉编号), 文本信息, 转换坐标
            stateMap, cur_state = {}, {}    # Graphics State 堆栈. 当前的状态. 目前而言, 主要就是存放tm,cm信息
                                            # stateMap={数字编号:{"tm":,"cm":...}}
            print(desfile)
            
            while ( True ):
                tmpbuf = self.file_tools.readLineST( streambuf )
                if ( not tmpbuf ):
                    break
                tmpbuf = tmpbuf.decode("utf-8").strip()
                    
                print(tmpbuf)
                if ( "BT" in tmpbuf ):     # 如果是 包含"BT"/"ET"
                    retbuf += self.processBT( tmpbuf, streambuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf )
                    #retbuf += self.processBT( tmpbuf, streambuf, cmap, cur_xy, textMap, cellMap, stateMap, cur_state )
                    
                if ( "BDC" in tmpbuf ) :     # 如果是 包含"BDC"/"EMC"   
                    retbuf += self.processBDC( tmpbuf, streambuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf )
                    #retbuf += self.processBDC( tmpbuf, streambuf, cmap, cur_xy, textMap, cellMap, stateMap, cur_state )

                # re 的处理应该在BT/ET, BDC/EDC 之外, 也就是单元格.
                if ( "re" in tmpbuf ) :     # 如果是 包含"BDC"/"EMC"   
                    self.processRE( tmpbuf, cellMap, cellIndexMap, cur_xy, tm )

                #if ( "cm" in tmpbuf ) :    # 
                #    self.processCm( tmpbuf, tm )

                if ( "Tf" in tmpbuf ) :
                    self.processTf( tmpbuf, tf )

                if ( "q" in tmpbuf or "Q" in tmpbuf ) :    # 
                    tm = {}

            
            retbuf = self.processTxtForTable( textMap, cellMap, cellIndexMap )  # 处理文本内容, 如果有表格, 则进行表格处理
        
            with open( desfile, "w") as fs:
                if ( retbuf ):
                    fs.write( retbuf )
                else:
                    fs.write( "没有数据！" )
            
            print("decode()!!!after write to file" )

        except:
            traceback.print_exc()
            print( "decode() Exception Error!" )


    '''
    /*
     * 16. processBT()
     *      处理 BT/ET 内的内容
     * 入口参数:
     *      streambuf           字节流映射文件 哈希表, 读取内容的时候需要.
     *      cmap                字符映射表 哈希表
     * 出口参数:
     *      无
     * 返回值:
     *      无
     * 说明:
     *      处理过程基本同BDC 一致， 就是内部不包含BT的判断, 而是包含了BDC处理的嵌套
     *      处理后的内容存放在哪儿？？？？？ 文件？？
     * 2016.12.12:
     *      Tm 的内容是转换坐标系. [a b c d e f], 定义一个list Tm, 存放最新的转换坐标
     *      Td/TD 的坐标实际为
     *           x' = a * x + c * y + e
     *           y' = b * x + d * y + f
     * depends on:
     *       self.processBDC(), .processRE(), /*processQ()*/
     *       self.hasTxtPosition(), .processTxtPosition(),  .hasText(), .processText(),
     *       self.file_tools.readLineST()
     *      
     * 
     */
    '''
    # cur_xy = {"cur_opr":,"x":x,"y":y,  "ox":ox,"oy":oy, "tm":{tm}}
    # textMap = {编号:{"xy":{"x":x,"y":y, "ox":ox,"oy":oy,"tm":{tm}},'txt':txt} }
    # cellMap = {编号:{'x':,'y':,'w':,'h':}}
    # tm = {'a':a, 'b':b, 'c':c, 'd':d, 'e':e, 'f':f}    # 一直存放的是最新的tm数据
    def processBT( self, buf, streambuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf ):
        try :

            retbuf = ""
            tmpbuf = buf
            print("--processBT()")
            print(cmaps.keys())
            while ( True ):
                if ( not tmpbuf ):
                    break
                
                # 1. 过滤 页眉，页脚， 水印
                #    判断是否包含  /Artifact && （/Top   /Bottom   /watermark）任一 
                #     如果包含， 则过滤后面的BDC, EMC 之间的内容
                # 2. 即便是页眉或页脚, 里面的坐标也要处理, 否则后面的坐标会出现错误.
                if ( ( "/Top" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) : 
                    # 页眉  , BDC 是起始标识
                    while ( tmpbuf ):
                        if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                            break
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        if ( self.hasTxtPosition( tmpbuf ) ) :
                            self.processTxtPosition( tmpbuf, cur_xy, tm  )
                        if ( "Tm" in tmpbuf ) :
                            self.processTm( tmpbuf, tm, cur_xy )
                    
                elif ( ( "/Bottom" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) : 
                    # 页眉  , BDC 是起始标识
                    while ( True ):     # 下面的循环判断比上面的循环判断可读性要高一点
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        if ( not tmpbuf ):
                            break
                        if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                            break
                        if ( self.hasTxtPosition( tmpbuf ) ) :
                            self.processTxtPosition( tmpbuf, cur_xy, tm  )
                        if ( "Tm" in tmpbuf ) :
                            self.processTm( tmpbuf, tm, cur_xy )
                    
                elif ( "BDC" in buf ):      # 一段文字  处理 BDC/EMC  文字部分
                    print("==BT=========:%s: =======" % tmpbuf )
                    retbuf += self.processBDC( tmpbuf, streambuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf ) # 调用 BT 的处理
                elif ( "re" in buf ):       # 58.08 323.96 124.82 19.02 re
                    # 如果 有 re 信息， 表示是表格, 获取cell 信息, 如果碰到Tm, 会置cur_cell=[:]
                    print("==RE=========%s=======" % tmpbuf )
                    self.processRE( tmpbuf, cellMap, cellIndexMap, cur_xy, tm )
                
                # 如有有q 信息, 那么表示保存当前的图形状态信息, 包括坐标信息, 然后到Q 再恢复
                #/* 暂时不处理q/Q, 因为re 使用的是绝对坐标
                #if ( "q" in buf ) :    # q
                #    self.processQ( streambuf )
                #}
                #*/
               
                print("==BDC=========%s=======" % tmpbuf )
                # 处理字体信息, 如果需要显示的话, 需要根据字体以及x坐标来计算空格位置
                if ( "Tf" in tmpbuf ) :
                    self.processTf( tmpbuf, tf )

                # 如果buf 有 文本位置信息, 则处理后获得当前的xy 坐标
                # 2016.12.13:
                #   不单独处理位置, 这儿只处理Tm 也就是转换坐标信息, 保证最新的转换坐标起作用. 文本的坐标在文本内部处理
                if ( self.hasTxtPosition( tmpbuf ) ) :
                    self.processTxtPosition( tmpbuf, cur_xy, tm  )

                if ( "Tm" in tmpbuf ) :
                    self.processTm( tmpbuf, tm, cur_xy )
                
                #if ( "cm" in tmpbuf ) :    # cm 处理与tm 处理相同, 调用Tm的处理方法既可
                #    self.processCm( tmpbuf, tm )

                if ( "q" in tmpbuf or "Q" in tmpbuf ) :    # 
                    tm = {}

                # 如果buf 有文本信息
                if ( self.hasText( tmpbuf ) ) :
                    retbuf += self.processText( tmpbuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf )
                

                if ( "ET" in tmpbuf ):  # 正文结束的标识
                    return retbuf
                    
                tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")   
            
        except:
            print( "processBT() Exception Error! 出错了:" )
            traceback.print_exc()

        return retbuf
    '''
    /*
     * 17. processBDC()
     *      处理 BDC/EMC 内的内容
     * 入口参数:
     *      streambuf           字节流映射文件 哈希表, 读取内容的时候需要.
     *      cmap                字符映射表 哈希表
     * 出口参数:
     *      无
     * 返回值:
     *      无
     * 说明:
     *      1. 过滤页眉/页脚, 如果有的话
     *      2. 如果有Td/TD/Tm/T*, 就获取位置信息, 并与之前处理的位置信息进行比较, 来判断是否要换行
     *      3. 如果有Tj,TJ, ', " , 表示文本内容, 摘取文本内容, 如果需要解码则进行解码
     *      4. 如果有re, 一般会对应f*, 也就是画矩形操作  
     *          x, y, width, height    re   // x,y 是左下角的坐标
     * depends on:
     *       self.processBT(), .processRE(), /*processQ()*/
     *       self.hasTxtPosition(), .processTxtPosition(),  .hasText(), .processText(),
     *       self.file_tools.readLineST()
     * 
     */
    '''
    def processBDC( self, buf, streambuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf ):
        try:
            retbuf = ""
            tmpbuf = buf
            print('-----processBDC():')
            print(cmaps.keys())
            while ( True ) :       
                # 1. 过滤 页眉，页脚， 水印
                #    判断是否包含  /Artifact && （/Top   /Bottom   /watermark）任一 
                #     如果包含， 则过滤后面的BDC, EMC 之间的内容  
                if ( ( "/Top" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ): 
                    # 页眉  , BDC 是起始标识
                    while ( tmpbuf ):
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        if ( "EMC" in tmpbuf.decode("utf-8") ):  # 页眉结束的标识
                            break
                        if ( self.hasTxtPosition( tmpbuf ) ) :
                            self.processTxtPosition( tmpbuf, cur_xy, tm  )
                        if ( "Tm" in tmpbuf ) :
                            self.processTm( tmpbuf, tm, cur_xy )
                    
                elif ( ( "/Bottom" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) :
                    # 页眉  , BDC 是起始标识
                    while ( True ):
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        if ( not tmpbuf):
                            break
                        if ( "EMC" in tmpbuf.decode("utf-8") ):  # 页眉结束的标识
                            break
                        if ( self.hasTxtPosition( tmpbuf ) ) :
                            self.processTxtPosition( tmpbuf, cur_xy, tm  )
                        if ( "Tm" in tmpbuf ) :
                            self.processTm( tmpbuf, tm, cur_xy )
                    
                elif ( "BT" in tmpbuf ) :    # 一段文字  处理 BDC/EMC  文字部分
                    retbuf += self.processBT( tmpbuf, streambuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf ) # 调用 BT 的处理
                elif ( "re" in tmpbuf ) :    # 58.08 323.96 124.82 19.02 re
                    # 如果 有 re 信息， 表示是表格, 获取cell 信息, 如果碰到Tm, 会置cur_cell=[:]
                    self.processRE( tmpbuf, cellMap, cellIndexMap, cur_xy, tm )
                    if ( "89.6 359 64.5 31.2 re" == tmpbuf ):
                        print("re ==========%s, tm=?" % tmpbuf )
                        print(tm)
                        print(cur_xy)
                        
                
                if ( "q" in tmpbuf or "Q" in tmpbuf ) :    # 
                    tm = {}

                '''
                // 如有有q 信息, 那么表示保存当前的图形状态信息, 包括坐标信息, 然后到Q 再恢复
                /* 暂时不处理q/Q, 因为re 使用的是绝对坐标
                if ( buf.indexOf("q") != -1 ) {    // q
                    processQ( streambuf )
                }
                */
                '''
                
                # 处理字体信息, 如果需要显示的话, 需要根据字体以及x坐标来计算空格位置
                if ( "Tf" in tmpbuf ) :
                    self.processTf( tmpbuf, tf )

                # 如果buf 有 文本位置信息, 则处理后获得当前的xy 坐标
                if ( self.hasTxtPosition( tmpbuf ) ):
                    self.processTxtPosition( tmpbuf, cur_xy, tm )
                    
                if ( "Tm" in tmpbuf ) :
                    self.processTm( tmpbuf, tm, cur_xy )
                
                #if ( "cm" in tmpbuf ) :    # cm 处理与tm 处理相同, 调用Tm的处理方法既可
                #    self.processCm( tmpbuf, tm )
                #    print("-----------cm------")
                #    print(tm)

                

                # 如果buf 有文本信息
                if ( self.hasText( buf ) ) :
                    retbuf += self.processText( tmpbuf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf )
                

                if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                    return retbuf
                    
                tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")    
            
        except:
            print( "processBDC() Exception errlr!出错了:")
        
        return retbuf

    def processTf( self, buf, tf ):
        retbuf = ""
        try:
            retbuf = buf.split(" ")[0]    #/C2_0    带一个斜杠, xref 中解析对象的时候, 字体名称不带斜杠, 需要去掉斜杠
            retbuf = retbuf[1:len(retbuf)]    # 去除斜杠
            tf["font"] = retbuf
        except:
            print("processTf() Exception Error!")
            traceback.print_exc()
        return retbuf

    '''
    /*
     *  18. hasText( buf )
     *          判断当前行是否有文本信息标识符  Tj / TJ/ ' / "
     *  入口参数
     *      buf     待处理的字符串
     *  出口参数
     *      无
     *  返回值
     *      False       没有包含文本信息标识符
     *      True        包含文本信息标识符
     *          
     */
    '''
    def hasText( self, buf ):
        if ( "Tj" in buf or "TJ" in buf or  "\'" in buf or "\"" in buf ): 
            return True
        else :
            return False

    '''
    /*
     *  19. processText( buf, curxy, pre_xy, cur_cell, pre_cell )
     *          处理文本信息, 判断是否需要换行, 是否需要解码
     *  入口参数:
     *      
     *  出口参数:
     *      
     *  返回值:
     *      
     *  说明:
     *      1. 判断cur_cell 与 pre_cell, 如果不为空, Y 相同, 则在同一行, 否则换行
     *         1.1 判断 cur_xy 是否在 cur_cell 中, 
     *      2. 只有处理文本以前, 才调用ifCRLF(),然后将cur_xy , cur_cell 保存到pre_xy, pre_cell,
     *         表示上一次处理文本的位置保存了。 才ifCRLF() 中处理位置相关的变量
     *  2016.12.10:
     *      改变实现思路. 新建一个textMap 字典, key:value=起始坐标:文本内容
     *      在re的处理中, 将结果存放在CellMap 字典中.
     *      等所有文本都解析出来后, 处理textMap 以及cellMap, 来进行文本合并以及换行的处理.
     * 2016.12.23:
     *      增加tf信息,实际上也就是字体名称.
     *      下一步用stateStack, cur_state的时候, 字体信息作为状态的一部分. 目前状态包括: 坐标, 字体.
     * depends on:
     *       self.ifCRLF(), .processTj(), .processTJ()
     *          
     */
    '''
    # cur_xy = {"cur_opr":,"x":x,"y":y,  "ox":ox,"oy":oy, "tm":{tm}}
    # textMap = {编号:{"xy":{"x":x,"y":y, "ox":ox,"oy":oy,"tm":{tm}},'txt':txt} }
    # cellMap = {编号:{'x':,'y':,'w':,'h':}}
    # tm = {'a':a, 'b':b, 'c':c, 'd':d, 'e':e, 'f':f}    # 一直存放的是最新的tm数据
    def processText( self, buf, cmaps, cur_xy, textMap, cellMap, cellIndexMap, tm, tf ) :
        retbuf = ""
        try:
            if ( tf["font"] in cmaps.keys() ):
                cmap = cmaps[ tf["font"] ].copy()
            else:
                cmap = {}

            # 2. 解码
            if ( "Tj" in buf ) :                        # Tj
                retbuf += self.processTj( buf, cmap )
            elif ( "TJ" in buf ) :                      # TJ
                retbuf += self.processTJ( buf, cmap )
            elif ( "\'" in buf ) :                      # '   单引号, 等同于T*  Tj 也就是移到下一行起始位置输出文本
                retbuf += "\r\n" + self.processTj( buf, cmap )
            elif ( "\"" in buf ) :                      # "   双引号,  使用了字间隔与字符间隔, 内容而言与单引号一样
                retbuf += "\r\n" + self.processTj( buf, cmap )

            print("解码前:%s" % buf )
            #print( "processText() end:" + retbuf + ":" )
            print(cur_xy)

            #if ( cur_xy['oy'] < cellMap[-1]['h'] ):
            # 如果是页眉, 则不添加到textMap 中, 也就是不处理, 但是返回数据, 为了调试方便
            #  这个处理要在最后处理, 因为页眉的文本在页眉cell之前, 这儿无法判断.
            #    return retbuf
            
            #key = str(len(textMap)+1)+":"+str(round( cur_xy['x']+cur_xy['ox'],3)) + ','+ str(round(cur_xy['y']+cur_xy['oy'] ,3) )
            
            key = len(textMap)+1
            #value = {"xy":cur_xy.copy(), 'txt':retbuf,'cell':-1, "o_xy":{"ox":cur_xy['ox'],"oy":cur_xy['oy']},"length":self.rlen(retbuf)}
            value = {'txt':retbuf,'cell':-1, "o_xy":{"ox":cur_xy['ox'],"oy":cur_xy['oy']},"length":self.rlen(retbuf), "pre":-1, "next":-1}
            # "next" 是个指针, 用来指向后一个txt, 后续处理由于会进行合并处理, 造成编号会有删减, 放next指针, 便于链起来, -1 表示结束
            if ( len(cellMap) > 1 ):   # >1 是为了跳过页眉
                ox,oy = cur_xy['ox'], cur_xy['oy']
                cellId = len(cellMap)-1
                cell = cellMap[cellId]
                cx,cy,cw,ch = cell['x'], cell['y'], cell['w'], cell['h']
                if ( ox >= cx and ox <= cx+cw and oy > cy and oy <= cy+ch ):
                    value['cell'] = len(cellMap)-1   # 减1 是因为cellMap 第一个是页眉的cell占用了,len()=2的时候才是编号为1的cell

                    cellIndexMap[cellId]["txtlist"].append( key )

                    maxlen = cellIndexMap[cellId]["maxlen"]     # cellIndexMap 项目的value是{"maxlen":,"col":,"row":,"txtlist":[]}
                    if ( self.rlen(retbuf) > maxlen ):    # 给cell的maxlen赋值
                        cellIndexMap[cellId]["maxlen"] = self.rlen(retbuf)         # 中文算2个字符长度的计算方法
            
            if ( key > 1): # 表示这不是第一个文本, 那么上一个next就是本文本， 本文本的上一个就是key-1
                textMap[key-1]["next"] = key
                value["pre"] = key-1
            textMap[key] = value
            # textMap = {编号:{"xy":{"x":x,"y":y, "ox":ox,"oy":oy,"tm":{tm}},'txt':txt} }
            #textMap[key] = retbuf

            #key1 = len(textIndexMap)+1
            #textIndexMap[key1] = key

            with open(self.tmpfile1, "a+") as fs:
                fs.write("--------------------\r\n")
                fs.write( buf+"\r\n")
                fs.write( str(key) + ":"+retbuf+"\r\n")
        except:
            print("processText() Exception Error!")
            traceback.print_exc()
            
        return retbuf

    # 将中文按2个字符长度计算字符串的长度，例如: b = '中文中文ab书', 长度算12
    # 99.rlen()
    def rlen(self, buf ):
        return int(( len(buf.encode("utf-8"))-len(buf) )/2 + len(buf) )  

    '''
    /*
     * 20. processTj( buf, cmap )
     *      处理含有 Tj 标识 的文字部分
     * 入口参数:
     *      buf     待处理的包含Tj 的未解码文本
     *      cmap    用于本页所有文本解码使用的cmap 哈希表
     * 出口参数:
     *      无
     * 返回值:
     *      解码后的文本
     * 说明:
     *      这儿只解析文本内容， 返回解码后的文本
     * 例子:
     <547F>Tj 482.391 0 TD<097E>Tj 482.391 0 TD<0D2D>Tj 480 0 TD<41F1>Tj 482.391 0 TD
<4AD2>Tj 482.391 0 TD<4AF1>Tj 482.391 0 TD<3E7C>Tj 480 0 TD<044A>Tj 482.391 0 TD
<1937>Tj 482.391 0 TD<1BA0>Tj 482.391 0 TD<0836>Tj 482.391 0 TD<34D7>Tj 480 0 TD
<41F1>Tj 482.391 0 TD<0868>Tj 482.391 0 TD<18C5>Tj 482.391 0 TD<4374>Tj 480 0 TD
<0E2A>Tj
     */
    '''
    def processTj( self, buf, cmap ) :
        
        print( "\r\nprocessTj() Begin:" + buf )
        retbuf = ""
        #print(cmap)
        try:
            if ( "(" in buf ):                              # 不需要解码
                p1, p2 = buf.index('('),  buf.index(')')    # 获取'(' , ')' 的位置
                retbuf = buf[ p1+1 : p2 ]           # 取小括号()中的内容
            elif ( "<" in buf ) :                           # 表示需要解码
                reg = re.compile(r'(<.+?>)')        # 需要解码的文本信息的正则表达式
                l = re.findall( reg, buf )          # 返回结果是各List, 以下同
                print(" processTj()需要解码的文本数量%d" % len(l) )
                tmpbuf = ""
                for item in l:                      #  逐条获取不需要解码的文本信息
                    i = 0            # 有可能是<41F7086E>, 即多个Unicode编码
                    while( i+4 < len(item) ):
                        tmpbuf += item[i+1:i+5]
                        i += 4

                print( "processTj() <>内的内容为:%s:" % tmpbuf )
                for i in range(0, len(tmpbuf) // 4 ):
                    retbuf += chr( cmap[ tmpbuf[ i*4:(i+1) * 4 ] ] )

            print( "processTj() 解码后:" + retbuf + ":" )
        except:
            print("processTj() Exception Error! 可能是txt 无法显示的utf8编码, 比如版权符号, 有对号的小方框等等. 不影响使用.")
            traceback.print_exc()
        return retbuf
    

    '''
    /*
     * 21. processTJ( buf, cmap )
     *      处理含有 TJ 标识 的文字部分
     * 入口参数:
     *      buf     待处理的包含Tj 的未解码文本
     *      cmap    用于本页所有文本解码使用的cmap 哈希表
     * 出口参数:
     *      无
     * 返回值:
     *      解码后的文本
     * 说明:
     *    1. TJ 类型, 表示有文字， 里面包含多个格式的文本
     * 例子:
     *    1.  [<41F7086E>-3<05192E37>-3<03C6>]TJ
     */
    '''
    def processTJ( self, buf, cmap ):
        retbuf = ""
        print( "\r\nprocessTJ()" + buf )
        try:
            if ( "(" in buf and  "<" in buf ):        #  既包含非汉字， 也包含汉字编码
                # 这种情况不知道有没有, 暂时列在这儿， 不处理, 目前没有发现这种情况出现
                print( buf + "===============================既包含<>,有包含()的TJ \r\n" )
            elif ( "(" in buf ) :                   # 不需要解码
                reg = re.compile(r'(\(.+?\))')      # 不需要解码的文本信息的正则表达式
                l = re.findall( reg, buf )          # 返回结果是各List, 以下同

                #print(" processTJ() 不需要解码的文本数量%d" % len(l) )
                retbuf = ""
                for item in l:                      #  逐条获取不需要解码的文本信息
                    retbuf += item[1:len(item)-1]
            elif ( "<" in buf ) :                   # 包含 < > 表示需要解码成unicode
                # 先将所有需要解码的编码合并在一起, 然后一起处理
                reg = re.compile(r'(<.+?>)')        # 需要解码的文本信息的正则表达式
                l = re.findall( reg, buf )          # 返回结果是各List, 以下同

                print(" processTJ() 需要解码的文本数量%d" % len(l) )
                print(l)
                tmpbuf = ""
                for item in l:                      #  逐条获取不需要解码的文本信息
                    i = 0            # 有可能是<41F7086E>, 即多个Unicode编码
                    while( i+4 < len(item) ):
                        tmpbuf += item[i+1:i+5]
                        i += 4

                print( "processTJ() <>内的内容为:" + tmpbuf )
                for i in range(0, len(tmpbuf) // 4 ):
                    retbuf += chr( cmap[ tmpbuf[ i*4: (i+1) * 4 ] ] )
                
            
            print( "processTJ() 解码后:" + retbuf + ":" )

        except:
            print("processTJ() Exception Error! 可能是txt 无法显示的utf8编码,print()绘出异常, 比如版权符号, 有对号的小方框等等. 不影响使用.")
            traceback.print_exc()
        return retbuf
    

    '''
    /*
     * 23. processRE()
     *      处理 re 内的内容
     * 入口参数:
     *      buf                 当前包含TD 的一行信息
     * 出口参数:
     *      cur_cell            哈希表, 记录单元格坐标 "x":x坐标值, "y":y坐标值, "w":width, "h":height
     * 返回值:
     *      无
     * 说明:
     *      如果有re, 则说明是表格, 记录Tj/TJ/'/" 之前的最新的re 的数据为最新的cell 信息。
     *  如果连续有多个re, 那么处理最新的re信息后, cur_cell 也存放的是最新的re信息
     *      如果碰到Tm, 会置cur_cell=[:], pre_cell=[:]
     *      x, y, width, height  re   ,  画一个矩形. x,y 是左下角坐标.
     *      RE 返回的是CELL 的词典, {'re1':[x,y,w,h],'re2',}
     * 2016.12.10:
     *      改变思路, 每次处理re的时候将获取的cell信息存放在一个cellMap中, 所有内容解析出来后,
     *      再结合 textMap和cellMap来处理换行以及跨表格文字的换行问题.
     *      1. 有些pdf文档中re 的x是负数, w 高达好几千, 例如:
     *              -1638.4 72 3795.5 39.1 re
     *      可能是用来控制的, 与内容无关, 可以过滤掉, 未来如果需要进行显示再处理
     *      2. 如果高度小于1, 可能是用来分隔页眉的, 例如:
     *          76.55 55.2 442.2 0.72 re
     *        这种高度时不可能有字体放入的.
     *      3. 获取所有的表格信息后, 还要进行一次过滤, 把包含表格的cell过滤掉, 目前发现只有一种情况会包含表格.
     *        整个页面边框有个表格, 这个表格会包含其它所有的合法表格(控制类re除外).
     *        目前简单处理, 第一个re 就是这种情况, 直接把第一个re过滤即可.
     *          0 0 595.3 841.9 re
     * 2016.12.21:
     *      re 也需要根据Tm 来进行坐标转换, 否则文本位置与表格位置就无法判断正确了.  不需要转换, 每次都是绝对坐标, 似乎与q/Q有关. 会清除之前的坐标转换信息???
     *      cellIndexMap[cellid] = {"maxlen":,"col":, "row":, "txtList":[]}
     * 2016.12.22:
     *      对一种极端情况进行容错. 当前cell完全在另一个有效cell之内, 则丢弃该cell
     * 2017.01.15:
     *      如果当前cell包含之前的某个有效cell, 则用当前cell 替代之前的有效cell
     */
    '''
    def processRE( self, buf, cellMap, cellIndexMap, cur_xy, tm ) :
        try :
            print("+++++++++processRE() being+++++++++" + buf)
            cur_cell = {}
            tmpbuf = buf.split(" ")
            for i in range( 0, len(tmpbuf) ): 
                if ( "re" in tmpbuf[i] ) :              # 如果找到re, 那么前面i-4, i-3, i-2, i-1就是x,y,w,h
                    cur_xy.clear()
                    tm.clear()
                    cur_cell["x"] = float( tmpbuf[i-4] )
                    cur_cell["y"] = float( tmpbuf[i-3] )
                    cur_cell["w"] = float( tmpbuf[i-2] )
                    cur_cell["h"] = float( tmpbuf[i-1] )

                    # x 坐标小于0可能是控制用的, h,w数值小于1可能是用来做分割线的, (x,y)=(0,0)从原点来时的表格也是控制用(页眉都不可能在原点)
                    # 把页眉也保留, 用来判断页眉文本
                    if ( cur_cell["x"] < 0 or cur_cell["y"] < 0 or cur_cell["w"] < 1 or ( cur_cell["x"]==0 and cur_cell["y"]==0) ):   # (0,0)仍然过滤, 暂时没想到怎么处理
                        return
                    if (  cur_cell["h"] < 1 ):  # 页眉的分割线
                        cellMap[-1] = cur_cell.copy()   # 这个是页眉分割线, 实际上是一个高度极小的表格.
                        cellIndexMap[-1] = {"maxlen":-1,"row":-1,"col":-1,"table":-1, "txtlist":[]}    # 页眉也统一初始化该数据, 虽然没用, 但是便于处理
                        return

                    # 2017.01.15:  过滤或替代无效的cell
                    self.filterCell( cellMap, cellIndexMap, cur_cell )
                    return
            
        except:
            print( "processRE() Exception error:" )
            traceback.print_exc()
            return

    
    '''
    /*
     * 23.1. filterCell()
     *       过滤无效的cell
     *  说明:
     *      有些cell 是无效的, 自身就在另一个有效cell之内。 丢弃即可
     *  2017.01.15:
     *      1. 当前cell 已经在之前的有效cell 内部, 则丢弃
     *      2. 如果当前cell 包含之前的 有效cell内部, 则用当前的cell 替代之前的有效cell   
     */
    '''
    def filterCell( self, cellMap, cellIndexMap, cur_cell ):
        try:
            length = len(cellMap)
            print("------ in filterCell ----")
            print( cellMap)
            cx, cy, cw, ch = cur_cell["x"], cur_cell["y"], cur_cell["w"], cur_cell["h"]
            if ( length > 1 ):    # 第一个是页眉, 有效的， 页眉的key 值是-1. 所以只需要判断大于1的情况即可, 第一个有效的cell的key值就是1, 同理后面的也一样
                #for k, v in sorted( textMap.items(), key=lambda d:d[1]['o_xy']['oy'], reverse = True ):

                for k, v in sorted( cellMap.items(), key = lambda d:d[1]['y'], reverse= True):
                    if ( k == -1 ):     #  跳过-1那个编号, 有可能没有页眉, 但是-1是保留给页眉的cell使用的
                        continue
                    px, py, pw, ph = v["x"], v["y"], v["w"], v["h"]
                    if ( ( cx>= px and cx+cw <= px+pw ) and ( cy >= py and cy+ch <= py+ph ) ):
                        # 1. x,y 范围都在pre_cell之内的话, 就判定为无效
                        return 
                    
                    print("cur=(%.3f,%.3f,%.3f, %.3f), 检查是否需要替换(%.3f,%.3f,%.3f, %.3f)" % (cx,cy, cw, ch, px, py, pw, py))
                    #if ( ( px>= cx and px+pw <= cx+cw ) and ( py >= cy and py+ph <= cy+ch ) ):
                    if ( (abs(px-cx)<1 or px >= cx )and ( abs(px+pw -cx-cw)<1  or px+pw <= cx+cw )and
                         ( abs(py -cy)<1 or py >= cy) and (abs(py+ph -cy-ch)<1 or py+ph <= cy+ch )):
                        # 前cell 包含之前的 有效cell内部, 则用当前的cell 替代之前的有效cell
                        print("cur=(%.3f,%.3f,%.3f, %.3f), 替换(%.3f,%.3f,%.3f, %.3f)" % (cx,cy, cw, ch, px, py, pw, py))
                        cellMap[k]={ "x":cx, "y":cy, "w":cw, "h":ch }
                        return
                
            cellMap[length] = cur_cell.copy()
            cellIndexMap[length] = {"maxlen":-1,"row":-1,"col":-1,"table":-1, "txtlist":[] }    # 缺省长度为-1, 没有对应的文本, 后续处理会增加文本编号

            with open("F:/F_T_tmp/tmp1/re.txt","a+") as fs:
                fs.write( "%-2d,re: x=%-8.2f,y=%-8.2f,w=%-8.2f,h=%-8.2f\r\n\r\n" % ( length,cur_cell["x"],cur_cell["y"],cur_cell["w"],cur_cell["h"] ))
                
        except:
            print("filterCell() Exception Error!")
            traceback.print_exc()

    '''
    /*
     * 24. processQ( streambuf )
     *      处理q/Q 的信息, q 保存图形状态, Q 恢复图形状态
     * 入口参数
     * 出口参数
     * 返回值
     * 说明:
     *      碰到q 后, 直接过滤后面的信息, 直到碰到Q. 主要是图形的处理, 对于本系统而言, 
     *      只关注内容信息, 所以可以过滤掉这些信息
     *      
     *      不行， 不能简单的过滤q/Q中间的内容, q/Q 中间可能会嵌套q/Q, 而且里面也可能有文字内容
     *      用list 来实现堆栈，堆栈里存放那个 pre_cell, pre_xy
     *      经过仔细分析页面信息, 发现q/Q 本质上用处不大, 因为re 都是绝对坐标
     *      暂时不处理q/Q
     */
    '''
    def processQ( self, streambuf ) :
        buf = self.file_tools.readLineST( streambuf ).decode("utf-8")
        
        while ( "Q" not in buf ) :
            # 如果没有碰到Q, 什么也不做, 继续读取下一行。 过滤掉q/Q之间的内容
            buf = self.file_tools.readLineST( streambuf ).decode("utf-8")
            continue

        return
    
    '''
    /*
     * 25. hasTxtPosition()
     *      判断目标字符串是否包含位置信息
     * 入口参数
     *      buf         待处理的字符串
     * 出口参数
     *      无
     * 返回值
     *      false       不包含位置信息
     *      true        包含位置信息
     * 注意:
     *      有些内容也可能包含 Td, TD 等操作符， 应该区别， 即文本内容里面的不进行处理 !hasText( buf )
     * 2016.12.10:
     *      我晕, 上面的处理逻辑错误了..... 在没有编码的情况下, buf 中不可能含有Td等, 而是编码信息,修改逻辑, 删除!hasText() 相关判断
     *      缺少了T* 和 Tm的逻辑判断 - -！
     */
    '''
    def hasTxtPosition( self, buf ):
        #print("\r\nhasTxtPosition():" + buf)
        #if ( not self.hasText( buf ) and ( "Td" in buf or "TD" in buf or "\'" in buf or '"' in buf ) ):
        if ( "Td" in buf or "TD" in buf or "\'" in buf or '"' in buf or 'Tm' in buf or 'T*' in buf ):
            #println "hasTxtPosition()" + buf 
            return True
        else:
            return False
      
    '''
    /*
     * 26. precessTxtPosition( buf, cur_xy )
     *      处理包含位置信息的字符串, 将位置信息记录在cur_xy 哈希表中, "x":x坐标值， "y":y坐标值
     * 入口参数
     *      buf         包含位置信息的字符串
     * 出口参数
     *      cur_xy      哈希表 "x":x坐标值， "y":y坐标值
     * 返回值
     *      无
     * 说明:
     */
    '''
    def processTxtPosition( self, buf, cur_xy, tm ) :
        print("processTxtPosition():" + buf)
        if ( "Td" in buf ) :
            self.processTd( buf, cur_xy, tm )
            return
        
        if ( "TD" in buf ) :
            self.processTD( buf, cur_xy, tm )
            return
        
        if ( "Tm" in buf ) :
            self.processTm( buf, tm, cur_xy )
            print("processTxtPosition()---- after processTM()")
            return
        '''
        if ( "cm" in buf ) :
            self.processCm( buf, tm )
            print("processTxtPosition()---- after processCm()")
            return
        '''
        if ( "T*" in buf ) :
            self.processTstar( buf, cur_xy )
            return
        
    '''
    /*
     * 27. processTd()
     *      处理 Td 内的内容
     * 入口参数:
     *      buf                 当前包含Td 的一行信息
     *      cmap                字符映射表 哈希表
     * 出口参数:
     *      cur_xy              哈希表, 记录坐标 cur_xy["x"], cur_xy["y"]
     * 返回值:
     *      无
     * 说明:
     *      Td 有多种可能性, 0 Tc 0 Tr 265 0 Td 或者 -135.68 -14.78 Td
     *      1. -135.68 -14.78 Td 在 51134 L115, 这个应该是相对坐标。。。
     *      2. 
     *      奇怪, Td 里面的数据到底是相对坐标？还是绝对坐标？？？
     *      3. 0 Tc 0 Tr 48.26 0 Td            50617  L41
     *      4. 0 Tr 144.54 0 Td                 50617 L44
     *      5. /TT0 9 Tf                        50617 L29
     *          529.68 51.72 Td
     *          (74)Tj
     *          1 0 0 1 538.68 51.72 Tm
     *          ( )Tj
     *      6. 不修改cur_cell, pre_cell 的内容.
     * 2016.12.12:
     *      修正实现方式, Td/TD中的坐标必须用Tm 中的矩阵进行转换, 例如:
     *        0.05 0 0 -0.05 80.52 146.45 Tm

     *        <0E2A>Tj 208.797 0 TD<4801>Tj 211.188 0 TD<31B0>Tj 208.797 0 TD<3020>Tj
     *      那么: 转换矩阵对应的[a b c d e f]=[0.05 0 0 -0.05 80.52 146.45]
     *      根据转换公式: (参见: PDF 1.7 Reference P208)
     *          x' = a*x + c*y + e
     *          y' = b*x + d*y + f
     *      则208.797 0 TD 实际的坐标为:
     *        x' = 0.05 * 208.797 + 0*0 + 80.52 = 184.9165 约184.917
     *        y' = 0 * 208.797 + (-0.05)*0 + 146.45 = 146.45
     *      现在判断文字前面的表格
     *         75.15 134.4 130 16.1 re
     *       75.15 < x' < 75.15+130=205.15
     *       134.4 < y' < 134.4+16.1 = 150.5
     * 2016.12.26:
     *      Td 的处理比较复杂.
     *      1. 如果Tm为空,  如果之前没有坐标, 则(ox,oy) = (x,y); 如果之前有坐标, 则(ox,oy) = (x,y)+(x',y')
     *      2. 如果Tm 不为空, (ox, oy) = (x,y) * tm, 然后 tm 置空
     *
     * depends on:
     *      self.getOriginXY()
     *   
     * 
     */
    '''
    def processTd( self, buf, cur_xy, tm ) :
        try :
            print("=================cur_xy--Begin------------")
            print(cur_xy)
            tmpbuf = buf.split(" ")
            for i in range( 0, len(tmpbuf) ): 
                if ( "Td" in tmpbuf[i] ) :     # 如果找到Td, 那么前面i-2, i-1就是x,y
                    x, y = float( tmpbuf[i-2] ), float( tmpbuf[i-1] )

                    if ( len(tm) == 0 ):      # tm 为空
                        if ( len(cur_xy) == 0 ):      # 之前没有坐标的话, 则现在的坐标是绝对坐标
                            cur_xy["x"], cur_xy["y"] = x, y
                            cur_xy["ox"], cur_xy["oy"] = x, y
                        else:                         # 之前有坐标, 则现在的坐标是相对之前坐标的相对坐标
                            cur_xy["ox"], cur_xy["oy"] = round(cur_xy["ox"] + x,3) , round(cur_xy["oy"] + y,3)
                            cur_xy["x"], cur_xy["y"] = x, y
                    else:                               # 有tm, 进行坐标转换, 转换结束后, tm 置空
                        cur_xy["x"], cur_xy["y"] = x, y

                        self.getOriginXY( cur_xy, tm )  # cur_xy["ox"], cur_xy["oy"]赋值
                        tm.clear()

                    cur_xy["OPR"] = "Td"
                    print("=================cur_xy--------------")
                    print(cur_xy)
                    return
                
        except:
            print( "processTd() Exception error:")
            traceback.print_exc()
            return
        
    
    '''    
    /*
     * 28. processTD()
     *      处理 TD 内的内容
     * 入口参数:
     *      buf                 当前包含TD 的一行信息
     *      cmap                字符映射表 哈希表
     * 出口参数:
     *      cur_xy              哈希表, 记录坐标 cur_xy["x"], cur_xy["y"]
     * 返回值:
     *      无
     * 说明:
     *
     *  2016.12.10:
     *     原来的处理有问题, :<0016>Tj 91.188 0 TD<0015>Tj
     * 
     */
    '''
    def processTD( self, buf, cur_xy, tm ) :
        try :
            tmpbuf = buf.split(" ")
            for i in range(0, len(tmpbuf) ):
                if ( "TD" in tmpbuf[i] ) :              # 如果找到TD, 那么前面i-2, i-1就是x,y
                    cur_xy["tm"] = tm.copy()
                    cur_xy["x"] = float( tmpbuf[i-2] )
                    cur_xy["y"] = float( tmpbuf[i-1] )
                    cur_xy["OPR"] = "TD"
                    
                    self.getOriginXY( cur_xy, tm )  # cur_xy["ox"], cur_xy["oy"]赋值
                    return
        except:
            print( "processTD() error:" )
            traceback.print_exc()
            return
        

    '''
    /*
     * 29. getOriginXY()
     *      获取Td/TD 坐标的Matrics 坐标，因为Td/TD 大部分情况是相对坐标. 
     * 说明:
     *      1. 该方法只有processTd()和 processTD() 调用
     *      2. Tm, re 本身是绝对坐标, 不会调用该方法
     *      3. T* 也不用调用该方法, 因为它直接换行了, 不用进行判断了。
     * 
     *      
     */
    '''
    def getOriginXY( self, cur_xy, tm ) :
        try:
            print("getOriginXY():-----------------------------======================================")
            print(cur_xy)
            print(tm)

            # 下面来获取ox, oy, 也就是参考坐标的原始坐标值(参照物), 如果x,y 本身就是绝对坐标,则ox,oy = 0,0
            if ( len(tm) == 0 ) :      # 如果没有tm, 也就是没有转换坐标, 则x,y 就是绝对坐标
                if ( "ox" not in cur_xy.keys() ):   # 如果该坐标是第一个坐标
                    cur_xy["ox"] = cur_xy["x"]
                    cur_xy["oy"] = cur_xy["y"]
                else:
                    cur_xy["ox"] += cur_xy["x"]
                    cur_xy["oy"] += cur_xy["y"]
            else :
                # x' = a*x + c*y+e,  y'=b*x+d*y+f
                cur_xy["ox"] = tm['a']*cur_xy['x'] + tm['c'] * cur_xy['y'] + tm['e']
                cur_xy["oy"] = tm['b']*cur_xy['x'] + tm['d'] * cur_xy['y'] + tm['f']

            cur_xy["ox"] = round( cur_xy["ox"], 3 )
            cur_xy["oy"] = round( cur_xy["oy"], 3 )
        except:
            print("getOriginXY() Exception Error!")
            traceback.print_exc()
            print(cur_xy)
            

    '''
    /*
     * 30. processTm()
     *      处理 Tm 内的内容
     * 入口参数:
     *      buf                 当前包含 Tm 位置信息 的一行信息
     *      cmap                字符映射表 哈希表
     * 出口参数:
     *      cur_xy              哈希表, 记录坐标 cur_xy["x"], cur_xy["y"]
     * 返回值:
     *      无
     * 说明:
     *      特别需要注意的是, Tm 是绝对坐标, 处理Tm时, pre_cell, cur_cell 就可以置为[;], preT_xy 也置空[:]
     *      也就是说后面需要以 Tm 的坐标为基准进行计算与判断
     * 2016.12.21:
     *      增加了cur_xy参数. 因为一旦碰到Tm, 那么之前的坐标都没用了. 需要按照新的转换坐标来计算
     *      碰到Tm后, 初始化 (x,y)= (0,0)*Tm= (e,f)
     *      似乎所有的Tm 都在BT/ET 中间. 或许 ET之后, 该Tm 就失效了.
     */
    '''
    def processTm( self, buf, tm, cur_xy ) :
        try :
            print("===========================-------------------------processTm()" + buf)
            tmpbuf = buf.split(" ")
            print(tmpbuf)
            
            for i in range(0, len(tmpbuf) ):
                if ( "Tm" in tmpbuf[i] ) :              # 如果找到Tm, 那么前面i-6, i-5, i-4, i-3, i-2, i-1就是a,b,c,d,e,f
                    tm['a']     = float( tmpbuf[i-6] )
                    tm['b']     = float( tmpbuf[i-5] )
                    tm['c']     = float( tmpbuf[i-4] )
                    tm['d']     = float( tmpbuf[i-3] )
                    tm['e']     = float( tmpbuf[i-2] )
                    tm['f']     = float( tmpbuf[i-1] )
                    print("===========================-------------------------processTm()")
                    print( tm )

                    cur_xy['x'] = cur_xy['ox'] = tm['e']
                    cur_xy['y'] = cur_xy['oy'] = tm['f']
                    cur_xy['tm'] = tm.copy()
                    return
            
        except:
            print( "processTm() error:" )
            return

    # 30.1 processCm()
    #     转换矩阵, 目前看作用和Tm类似, 回头再深研究
    def processCm( self, buf, cm ) :
        try :
            print("===========================-------------------------processTm()" + buf)
            tmpbuf = buf.split(" ")
            print(tmpbuf)
            
            for i in range(0, len(tmpbuf) ):
                if ( "cm" in tmpbuf[i] ) :              # 如果找到cm, 那么前面i-6, i-5, i-4, i-3, i-2, i-1就是a,b,c,d,e,f
                    cm['a']     = float( tmpbuf[i-6] )
                    cm['b']     = float( tmpbuf[i-5] )
                    cm['c']     = float( tmpbuf[i-4] )
                    cm['d']     = float( tmpbuf[i-3] )
                    cm['e']     = float( tmpbuf[i-2] )
                    cm['f']     = float( tmpbuf[i-1] )
                    print("===========================-------------------------processTm()")
                    print( cm )
                    return
            
        except:
            print( "processCm() Exception error:" )
            traceback.print_exc()
            return
        
    '''
    /*
     * 31. processTstar()
     *      处理 T* 内的内容
     * 入口参数:
     *      streambuf           字节流映射文件 哈希表, 读取内容的时候需要.
     *      buf                 当前包含T* 的一行信息
     *      cmap                字符映射表 哈希表
     * 出口参数:
     *      cur_xy              哈希表, 记录坐标 cur_xy["x"], cur_xy["y"]
     * 返回值:
     *      无
     * 说明:
     *      T*   直接到下一行的起始位置
     *2016.12.13:
     *    这个处理需要完善？？？？？
     * 
     */
    '''
    def processTstar( self, buf, cur_xy) :
        try :
            tmpbuf = buf.split(" ")
            for i in range( 0, len(tmpbuf) ): 
                if ( "T*" in tmpbuf[i] ) :              # 如果找到T*, 那么前面i-2, i-1就是x,y
                    cur_xy["x"] = 0         
                    cur_xy["y"] = cur_xy["y"] + 1       # 设+1 表示与上次处理的位置相比, 下移了, 那么就是下一行
                    cur_xy["OPR"] = "T*"
                    
                    # 注意， 上面的操作是假设T* 不会是第一个位置操作符， 目前测试也
                    # 确实没有第一个的情况, 但是如果真有T*是第一个位置操作符, 就会出异常
                    # 因为这个时候pre_xy["x"]等访问是无效的。
                    return
        except:
            print( "processTstar() error:" )
            return

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
                    retbuf += self.buildTableTxt( textMap, tableMap[tableid], cellMap, cellIndexMap, colIndexMap, rowIndexMap )
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
                        if ( i == 1 or ( cur_cells[i-2] in par_cells ) ):  # 前一个cell 是母行的话, 需要应该用"|     "
                            retbuf += "|" + col_len * " "
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
                            retbuf += "|"
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
    

#pdf = None
pdf = pdfService()
# 0773 是元, 5143， 但是266中0779 是5149。。。。   0779 是光   对应5143, 所以那一页用那一页的cmap, 不能混

#？？ 为什么第一次运行第一次的时候解码会提示对应编码不存在? 第二次就运行正常了? 似乎是残留内存没有更新的问题? 但是是重新运行的, 怎么会有残留？
# 不是很稳定, 有时候有一部分, 有时候会多一点。。。。。。 难道是中文引起的问题?
# Cmap 的解析出现了问题, 解决了。。
#pdf.parsePDF('F:/F_T_tmp/1202.pdf', '3')
#pdf.parsePDF('F:/F_T_tmp/1218.pdf', '3')
#pdf.parsePDF('F:/F_T_tmp/1.pdf', '1')
#pdf.parsePDF('F:/F_T_tmp/2.pdf', '1')
#pdf.parsePDF('F:/F_T_tmp/0106.pdf', '1')
#pdf.parsePDF('F:/F_T_tmp/0109.pdf', '1')
pdf.parsePDF('F:/F_T_tmp/0114.pdf', '1')
