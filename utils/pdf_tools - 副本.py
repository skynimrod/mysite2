# -*-  coding: utf-8  -*-

# pdf操作工具
# 坐标系的原点:  左上角是(0,0)
# 1. parsePDF()  -- getStartXrefPos(), getXREF(), getPages(), getCmapList, getCMAPs()
# 2. getStartXrefPos()
# 3. getXREF()  ---- getTrailer()
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
# 22. ifCRLF() ---
# 23. processRE()
# 24. processQ()
# 25. hasTxtPosition()
# 26. precessTxtPosition()
# 27. processTd()
# 28. processTD()
# 29. getOriginXY()
# 30. processTm()
# 31. processTstar()


import zlib
import re
import sys
import traceback
from file_tools import util_fileService

class pdfService():

    def __init__(self):
        self.tmpfile1 = "f:/F_T_tmp/tmp1/tmp.txt"
        self.file_tools = util_fileService()
    
    '''
     * 解析 PDF文件， 参见: Java/senior/pdf文件
     * 1. parsePDF()
     *
     * 2016.05.01  
     *          从 util_fileService 中拆分出来，主要处理步骤如下:
     *      1. 获取PDF 文件的trailer, 调用getTrailer()
     *      2. 对xref 进行预处理。由于采用多线程机制来提高处理效率， 可以先把部分重要
     *      的信息通过预处理先获得：preGetXref()
     * 2016.05.07:
     *      原来的解析方法有缺陷，xref 的处理有问题, 进行改进。每个xref都有一个trailer。
     *      1. 废弃 preGetXref(), 使用新的getXREF(), 
     *      2. 废弃getTrailer(), 使用 getTrailerx(), 这个方法仅在 getXREF()中使用.
     *      3. 解析步骤为:
     *          a. 获取xref. --> getXREF() { gettrailerx() }
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
     *      1. getStartXrefPos()
     *      2. getXREF()
     *      3. getPages()
    '''
    def parsePDF( self, srcFile ):

        self.file_tools.initReadFileMap( srcFile )
        
        xref, trailer, pages, posmap = {}, {}, {}, {}

        # 获取startxref 的内容, 也就是第一个xref 的位置
        start_pos = self.getStartXrefPos()
        
        if ( start_pos < 0 ):  # 容错处理 
            return -1
        
        posmap["curpos"] = start_pos
        xref["retcode"] = -1
        xref = self.getXREF( posmap, xref, trailer )
        a = xref['1']
        print(a)
        print(type(a))
        
        #print(xref)
        print( sorted( xref.items(), key=lambda d:d[0]) ) # 按键值进行排序
        
        if ( xref["retcode"] < 0 ):   # 容错处理
            print( "??? 出错了？")
            return -1
        
        print( trailer )
        
        # 获取最原始的页面对象信息. Root 对应的pages 中的页面信息.
        self.getPages( trailer["Root"], pages, xref )
        
        if ( len(pages) <= 0 ):         # 容错处理
            return -1
        
        print( sorted( pages.items(), key=lambda d:d[0]) )
        '''
        /*
         * 测试代码， 打印pages 的内容 以及 xref 对象的描述内容
         */
        
        '''
        with open("F:/F_t_tmp/tmp1/Rowpages.txt","w") as fs:
            for key in pages: 
                buf =  self.getObjContent( pages[key], xref )
                fs.write( pages[key] + "|" + buf + "\r\n\r\n" ) 

        with open("F:/F_t_tmp/tmp1/xrefAll.txt","w") as fs:
            fs.write("len(xref) = %d\r\n" % len(xref) )
            for key in sorted(xref.keys()):
                buf =  self.getObjContent( key, xref )
                #print(key)
                #print(type(key))
                fs.write( key + "||" +buf + "\r\n\r\n" ) 
        '''
        
        // 1. 分析pages 的对象内容(这个哈希表中的对象全部是叶子对象), 如果有Type0则存放在
        // cmaplist 哈希表中    页号:cmap对象1  cmap对象2...,   例如: "1":"5 9"
        // 注意: cmaplist 的第一项是所有cmap对象的汇总, 如: "total":"5 9 27"
        
        
        // 2. 通过cmaplist, 处理total中的每一个cmap对象, 将获取的映射表存放在cmaps哈希表中
        // 内容如下:   "5":cmap 哈希表，  注意: value 是一个哈希表， 存放的是映射内容。
        //     类似:"0528":2382,  注意映射表中的值是 数字, 是为了方便后续处理. 
        // 3. 1与2  放在一个方法里实现
        // cmaplist 的key值 是页面对应的叶子页面的对象编号, 不是页号, 对应的是pages哈希表中的value
        '''
        cmaplist, cmaps, contentMap ={}, {}, {}
        self.getCmapList( pages, xref, cmaplist, contentMap) 
        
        
        
        # log.info xref 
        print( "========= xref size ====%d", len(xref) )
        print( "========= pages size ====%d", len(pages) )
        print( "========= cmaplist size ====%d" , len(cmaplist) )
        print( "========= cmaplist ====")
        print( cmaplist )
        print( "========= contentMap ====%d", len(contentMap) )
        print( contentMap )

        
        self.getCMAPs( cmaplist, xref, cmaps ) 

        
        pageno = "3"
        with open(self.tmpfile1, "w") as fs:
            fs.write("------第3页测试--------------\r\n")
            
        self.processPage( pageno, pages, xref, cmaps, cmaplist, contentMap, "F:/F_t_tmp/tmp1/"+pageno + "_content.txt")
        

    '''
     * 2. getStartXrefPos()
     *      获取startxref 的值， 也就是第一个xref 的物理位置
     *  入口参数:
     *      无
     *  出口参数:
     *      无
     *  返回值:
     *      -1    文件格式错误
     *      >0    startxref 的物理位置
    '''
    def getStartXrefPos( self ):
        try:
            self.file_tools.seek( self.file_tools.getFileLength() - 48 )  #参数为要定位的文件的字符位置，0代表定位在文件的开头

            while(True): #逐行读取该文件，如果定位到文件中一行的中间，则只读取从定位的位置开始的后半部分
                temp = self.file_tools.readLine()
                
                if ( not temp ):   # is null 不行, ！= null 也不行
                    return -1
                
                if ( "startxref" in temp.decode("gbk") ):  # 表示找到了startxref
                    #print("找到了！")
                    temp = self.file_tools.readLine()      # startxref 的下一行包含位置信息
                    #print( temp )
                    startxrefpos = int( temp )
                    
                    return startxrefpos
            
        except:
            print( "getStartXrefPos() Exception error!")
            return -1

    '''
     * getXREF()
     *     入口参数:
     *          posmap  (xref位置,一个哈希表，取pos["curpos"]), xref, trailer
     *     出口参数:
     *          trailer, xref
     *     返回值: 
     *          无
     *              
     *      2016.05.06    重新实现交叉引用表的获取。 处理PDF 1.4 版本的一些文件时发现,
     *       1. xref 的完整构成是   xref + trailer.  如果有多个xref, 那么就有多个trailer.
     *          从最后的trailer 后面的startxref 来获取第一个xref, 然后获得最初的交叉引用表
     *          信息， 然后是一个对应的trailer, 处理这个trailer, 如果有prev, 那么继续下一个
     *          xref 的定位并处理， 然后获得对应的trailer, 再判断是否有prev, 一次类推， 直到
     *          最后一个trailer 没有prev, 表示处理结束.  需要注意的是， 最后的交叉引用表中的
     *          对象的位置信息覆盖之前的xref 中的对象的位置信息。
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
     *               prev 是互相一样的， 那么会造成处理xref 死循环。 这儿要判断后续新的xref 位置是否
     *               已经被处理过了, 如果被处理的话, 也就是在pos 中应该有对应的值， 那么就说明文件出错了，
     *               直接退出不再处理. 
     *               
     *               getXREF( pos, xref, trailer )
     *           3. while ( buf = readline() 不包含 trailer ) { // 不包含trailer 也就是没有结尾
     *                  // 循环处理, 确认所有的对象信息都处理到了
     *              }
     *              // 下面处理trailer
     *              trailer["Root"], trailer["Prev"]...
     *              if ( trailer["Prev"] 有效值 ) {
     *                  xref += getXREF( pos, xref, trailer )
     *                  // 注意， 这儿传入trailer， 那么最后处理的trailer 会覆盖前面处理的trailer 的元素内容. 
     *              }
     *              
     *              return xref
     *           4. retcode 错误代码说明: (只有等于0的时候xref才是正确的)
     *                  -40421      xref 的位置信息有误， 可能文件已经被破坏
     *                  -40422      xref 格式有误， 可能不是以xref开头
     *                  -40423      xref 格式有误,  第二行不是 起始对象编号 对象数量
     *                  -40431      xref 格式有误,  traile格式有误
     *           5. 注意， 这是个嵌套函数， 如果定义了返回值， 最后一定不要忘记返回xref. 
     *              否则groovy 并不会提示错误， 但是到最后由于没有返回， 调用的时候如果用了赋值， 可能会赋值null
    '''
    def getXREF( self, posmap, xref, trailer ):
        buf = ''
        xref["retcode"] = -1
        # 如果posmap["curpos"] 已经处理过, 即在后面的元素中已经有值了，则说明文件被破坏了, 会造成死循环
        
        tmpmap = posmap.copy()
        # tmpmap 是个临时字典, 用来判断posmap 除了curpos 外, 有没有重复的地址. 直接赋值的话, 修改tmpmap等同于修改posmap
        if ( "curpos" in tmpmap.keys() ):
            del(tmpmap["curpos"])

        if ( "curpos" not in posmap.keys() or posmap["curpos"] in tmpmap.values() ) :
            print( "posmap错了1？" )
            return xref
        
        # 将当前的posmap["curpos"] 添加到posmap哈希表中, key 和  value 一致。 主要是value
        posmap[ posmap["curpos"] ] = posmap["curpos"]
        
        cpos = -1      # 用来记录xref 第一个对象信息的位置, 所有对象的位置信息可以通过计算过的
        
        try:
            self.file_tools.seek( posmap["curpos"] )
            # 第一行
            buf = self.file_tools.readLine()
            if ( not buf or "xref" not in buf.decode("gbk") ): # 如果没有第一行或者第一行不是xref ，格式出错
                xref["retcode"] = -40421
                print( "第一行错了？" + buf.decode("gbk") )
                return xref
            
            # 循环处理第二行和后续的， 如果后续的trailer 里面有prev, 则需要嵌套调用getXREF()
            while ( True ):
                buf = self.file_tools.readLine()
                if ( not buf ):
                    break
                
                # 如果是trailer ()  则跳出循环， 直接处理trailer, 如果没有trailer , 后续的判断会出错， 返回-40423错误
                buf = buf.decode("gbk")
                if ( "trailer" in buf   ):
                    print("发现trailer："+ buf)
                    break  
                
                tmp = buf.split(" ")
                if ( len(tmp) != 2 ):     # 如果不是5267 1 之类的格式(起始对象编号 对象数量), 格式出错
                    xref["retcode"] = -40422
                    return xref
                
                firstObj    = int( tmp[0] )    # 起始对象编号
                objSum      = int( tmp[1] )    # 对象数量

                if ( objSum < 1 ):       # 这种情况几乎不可能， 这儿是为了容错
                    xref["retcode"] = -40424       # 尽量用xref["retcode"], 这儿用这种方式， 是为了演示一种访问方式
                    return xref
                
                
                cpos = self.file_tools.getPosition()
                for i in range(0, objSum) :
                    self.file_tools.seek( cpos + i * 20 )
                    buf = self.file_tools.readLine().decode("gbk")   # 获取的应该是 0000000016 00000 n类似格式
                    tmp = buf.split(" ")           #
                    xref[ str(firstObj+i) ] = int( tmp[0] )    # tmp 的第一个元素就是obj在文件中的实际位置 
                
                # 处理完一个后， 如果有多个映射描述, 则继续while()大循环处理
                
            xref["retcode"] = 0

            # 这儿处理trailer, 如果有Prev, 则需要嵌套调用 getXREF(), 根据前面的处理,
            #  下一行读到的就是traier的内容
            if ( "Root" not in buf ):  # 如果trailer.<<...>>格式的话, trailer的内容实际上在下一行
                buf = self.file_tools.readLine().decode("gbk")
                print("buf="+buf)

            trailer = self.getTrailer( buf, trailer )
            print(trailer)

            if ( "Prev" not in buf ):
                # 如果trailer 不包含 Prev项，表示这是最后一个xref了
                print("已经处理完了最后一个xref")
                return xref

            if ( trailer["retcode"] < 0 ) :
                print("trailer 错了？" )
                print(trailer)
                xref["retcode"] = -40431
                return xref 
            
            if ( trailer["Prev"] ) : 
                print( "嵌套调用前: Trailer：" )
                print( trailer )
                posmap["curpos"] = trailer["Prev"]
                xref = self.getXREF( posmap, xref, trailer )   # 不用返回值也可以
            
            
            print( "最后" )
            print( xref )

            #trailer = trailerBAK.copy()   #
            print("==end==")
            print(trailer)
            
            return xref         # 这一句千万不要忘了， 否则groovy 不会提示错误
        except:
            print( "getXREF() Exception Error" )
            return xref
    
        

    '''
     * 4. getTrailer()
     * 2016.05.07
     *    由于xref 的处理方式发生变化, 原来的处理方式有缺陷, trailer 只是xref的一部分
     *       -40411    文件格式非法， trailer 格式错误, 没有找到startxref信息
     *       -40412    文件格式非法， trailer 格式错误, 没有找到trailer信息
     *    1. 处理Trailer, 
               <</Size 51387/Root 1 0 R/Info 50568 0 R/ID[<BE239411BFD7D4D9318C29408037556>
               <5CA7DFC3C76C2F42985CAE05DBD580F9>]/Prev 3275241/XRefStm 771024>>\r\n
     *      获取  Size, Root, Info, ID, Prev, XRefStm  6项 数据. 存放在 哈希表trailer 中的同名key的value 中
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

            # 以下的解析方法 不采用， 是为了防止出现顺序变化后，需要更新代码， 提高兼容性
            # 因为有些项目是可选的， 比如 Info, ID
            #def keys =["1":"Size","2":"Root","3":"Info","4":"ID", "5":"Prev","6":"XRefStm"]
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
                    flag = true
                
                elif ( "XRefStm" in item ):   # XRefStm 项
                    trailer["XRefStm"] = item.split(" ")[1]
                
            
            if ( not flag and "Prev" in trailer.keys() ):       # 如果该trailer,没有Prev, 则删除Prev项， 防止沿用之前的内容.
                del( trailer["Prev"] )
            
            trailer["retcode"] = len(trailer)     # 这儿的返回值是获得的有效项目的数量(包括retcode本身)
            
            print( trailer )
            print( "trailer.retcode=%d" % trailer["retcode"] )
            
        except:
            print("getTrailer() Exception Error!") 
        
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
     *          xref    哈希表， 存放的是所有对象的物理位置信息
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
    def getPages( self, root, pages, xref ) :
        
        try :
            print("====1=====getPages(), root="+ root)
            print(type(root))
            # 获取 Root 对象的信息
            tmp = self.getObjContent( root, xref )
            print(tmp)
            print( "root("+root+")位置: "+ str(xref[root]) +"| 内容:" + tmp )
            
            obj = ''         # 字符型
            # 获取Pages 对象的编号
            items = tmp.split("/")
            for item in items :
                if ( "Pages" in item ):     # 表示找到了包含Pages 的项目
                    obj = item.split(" ")[1]        # Pages 对应的对象编号
                    break
                
            print( "getPageleaf()前 len(pages)=%d Pages=%s" % (len(pages),obj ))
            self.getPageleaf( obj, xref, pages )
            print( "getPageleaf()后 len(pages)=%d" % len(pages) )
            return 0
            
        except:
            print("getPages() Exception Error.")
            return -1
        
    
        
    '''
     * 6. getObjContent()  
     *      根据对象编号获取对象的内容, 使用内存映射文件 
     * 入口参数:
     *      obj     是整数字符串 ， 对应的是对象编号
     *      xref    xref哈希表， 存放的是 对象编号:对象物理位置
     * 返回:
     *      对象的文字描述内容部分.
     * 说明:
     *      对象的描述部分， 第一行是 3 0 R , 也就是对象编号等信息, 直接过滤即可. 
     *      第二行才是对象的描述性文本内容.
     * 调用的外部方法有:
     *      1. seek() ------------------>util_fileService
     *      2. readLine() -------------->util_fileService
     * 调用的类对象内部的方法有:
     *      1. getObjPosInXref()
    '''
    def getObjContent( self, obj, xref ):
        content = ""
        try:
            if ( len(xref) == 0 ):
                return content
            self.file_tools.seek( xref[obj] )
            self.file_tools.readLine()
            content = self.file_tools.readLine().decode("gbk")
        except:
            print( "getObjContent 出错了:" )
        
        return content


    '''
     * 7. getPageleaf() 
     *      获取页号对应的内容对象, 结果存放在pageLeafs哈希表中
     *      附加功能是同时将该内容对象使用的cmap也获取后存放在cmaplist哈希表中(英文文件没有type0字体，也就是没有cmap)
     * 入口参数:
     *      pageObj     页对象编号字符串, 例如 "3"
     *      xref        交叉引用表, 哈希表, 用来检索对象的物理位置
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
    def getPageleaf( self, pageObj, xref, pageleaf ):
        try:
            retcode = -1
            
            #获取指定的页对象的描述信息， 例如:
            # 5251||<</Count 100/Kids[5252 0 R 5253 0 R 5254 0 R 5255 0 R 5256 0 R 5257 0 R 5258 0 R 5259 0 R 5260 0 R 5261 0 R]/Parent 5250 0 R/Type/Pages>>
            buf = self.getObjContent( pageObj, xref )
            #print( "1.buf=" + buf )
            if ( "Kids" in buf ):
                tmp = buf.split("/") 
                kidscount, kidStr = 0, ''
                for item in tmp:
                    if ( "Count" in item ):
                        kidscount = int( item.split(" ")[1] )        # buf[0] = "<<", 所以跳过
                    
                    elif ( "Kids" in item ):
                        item = item.strip()                 # 先删除前后的空格
                        kidsStr = item[6: len(item)-1]         # 跳过Kids[ 和最后的 ]
                
                items = kidsStr.split(" ")        
                length = len(items)
                for i in range(0, length // 3 ): # 不能用kidsCount 否则会数组溢出
                    obj = items[ i * 3 ]          # 对象编号
                    if ( list(pageleaf.values()).count( obj ) >=1  ):  # dict.values() 本身不是list， 而是dict_values, 需要转换为list类型
                        print( "该叶子被重复使用了(under "+ pageObj + "),leaf=" + obj )
                        print( pageleaf )
                        return -1
                    self.getPageleaf( obj, xref, pageleaf )
                
            elif ( "Contents" in buf ):    # 只有含有 Contents 的对象才是真正的叶子对象
                #print("=====|||"+buf+":pageObj="+pageObj)
                if (  list(pageleaf.values()).count( pageObj ) >=1  ):  # 如果已经处理过, 就不再处理.
                    print( "pageleaf已经有了" + pageObj )
                    return -1
                   
                print( "|| 这是一个叶子:" + pageObj )
                pageleaf[ str( len(pageleaf)+1 ) ] = pageObj
                #print( sorted( pageleaf.items(), key=lambda d:d[0]) )
            
            return 0

        except:
            print( "getPageleaf() Exception Error"  )
            return -1
        
        
        return 0
    
    '''
     * 8. getCmapList()
     * 
     * 入口参数:
     *      pages
     *      xref
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
     * Depends ON:
     *      self.isType0()
    '''
    def getCmapList( self, pages, xref, cmaplist, contentMap):
        try:
            cmaplist["total"] = ""      # cmaplist 哈希表的total 项是所有cmap对象的汇总， 便于后续处理获得CMAP
            
            for key in pages:
                buf = self.getObjContent( pages[key], xref ).strip()
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
                            contentMap[ pages[key] ] = tmp1.strip()
                        else:
                            contentMap[ pages[key] ] = tmp[i].split(" ")[1]    # 类似 Contents 101 0 R
                        
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
                        tmp1 = ""       # 存放Type0 的对象编号, 空格分隔
                        i += 1      # Font 的下一项及后面的, 就是对象编号 比如 C2_0 5 0 R , TT0 10 0 R等
                        while ( i < len(tmp) ):
                            #println "具体字体:" + tmp[i] + "|" + tmp[i].split(" ")[1] + "|"
                            obj =  tmp[i].split(" ")[1]     # C2_0 5 0 R 拆分后, 第二个元素就是对象编号
                            if ( self.isType0( obj, xref ) ) :   # 判断是否是Type0 字体
                                tmp1 += obj + " "
                                if ( obj not in cmaplist["total"] ):  # 如果没有在total 项中登记, 则添加
                                    cmaplist["total"] += obj + " "      # 后面的空格是分隔符
                                
                            if ( ">>" in tmp[i] ) :   # 最后一个字体，字体结束, 跳出本循环
                                break
                            
                            i += 1
                        # 删除尾部多余的空格
                        cmaplist[ pages[key] ] = tmp1.strip()
                    
        except:
            print( "getCmapList() Error:" )

    '''
    /*
     * 10. getCMAPs()
     *      获取所有的CMAP对象额编解码信息，并存放在哈希表中.  "对象编号":编解码映射哈希表
     * 入口参数:
     *      cmaplist
     *      xref
     * 出口参数:
     *      cmaps
     * depends on:
     *      self.getObjContent()
     *      self.getItemOfObj()
     *      self.procType0Stream()
     */
    '''
    def getCMAPs( self, cmaplist, xref, cmaps ):
        try:
            # 如果cmaplist["total"]里面没有对象编号, 说明没有中文等需要编解码的内容,不需要cmap, 直接返回
            print( 'begin of getCMAPs() ')
            if ( len( cmaplist["total"].strip() ) == 0 ) :      
                return 
                
            print( 'next of getCMAPs() %s---------------' % cmaplist["total"] )
            tmp = cmaplist["total"].strip().split(" ")   # cmaplist 哈希表的total 中存放的是cmap 对象的汇总，注意要删除后面的空格, 否则会出现空格作为对象编号的错误异常, 且不易发现
            length = len(tmp)
            print(tmp)
            for i in range(0, len(tmp) ):           # 每一项是一个cmap 对象编号字符串
                obj = tmp[i]                      # 存放对象编号
                # 5||<</BaseFont/ABCDEE+#CB#CE#CC#E5/DescendantFonts 6 0 R/Encoding/Identity-H/Subtype/Type0/ToUnicode 50569 0 
                content = self.getObjContent( obj, xref )      # 获取cmap 对象的描述信息
                #print("内容对象(%s)(%d)的描述: %s" % ( obj, xref[obj], content ) )
                if ( "ToUnicode" not in content ) :        # 如果该cmap 信息不包含"ToUnicode"
                    print( "CMAP:" + obj + ":Error 1, no ToUnicode" )
                    print(content)
                    return                            # 继续处理后面的CMAP

                content = self.getItemOfObj( obj, xref, "ToUnicode" )      # 存放 对象的描述信息
                if ( content == "" ) :                #说明没有找到ToUnicode项， 出错了
                    print( "CMAP:" + obj + ":Error 2, no ToUnicode" + "content=:"+ content )
                    return                            # 继续处理后面的CMAP
                
                # 获取CMAP stream 对象编号
                tmpobj = content.split(" ")[1]      # ToUnicode 50569 0 
                #print( content )
                #print( tmpobj )
                #cmap = {}
                cmap = self.procType0Stream( tmpobj, xref )  # cmap 是dict 字典
                print( "cmap(" + obj + "):"+tmpobj+"的映射内容为:" )
                #print( cmap )
                cmaps[obj] = cmap
            
            print( "所有的映射内容为：" )
            #print( cmaps )
            print( 'next of getCMAPs() %s' % cmaplist["total"] )
        except:
            print( "getCMAPs() Exception Error:" )

    

    '''
    /*
     * 9. isType0()
     *      判断指定对象是否是Type0 对象, 也就是CMAP 对象
     * 入口参数:
     *      obj     对象编号字符串
     *      xref    交叉引用表, 哈希表， 对象编号(字符串): 对象位置(数字)
     * 出口参数:
     *      无
     * 返回值
     *      true    是 Type0 对象
     *      false   不是 Type0 对象
     */
     '''
    def isType0( self, obj, xref ):
        try:
            buf = self.getObjContent( obj, xref )
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
     *      xref        交叉引用表, 哈希表
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
    def getItemOfObj( self, obj, xref, item, splitchars = "/" ) :
        try:
            objcontent = self.getObjContent( obj, xref )
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
    # depends on:
    #     getItemOfObj(), decompress(),
    #     file_tools.read(), .initStreamBuf(), .readLineST()
    def procType0Stream( self, obj, xref ) :
        cmap = {}
        
        print( "procType0_1()#####对象编号为：" + obj )
        try :
            # 50569||<</Filter/FlateDecode/Length 7645>>stream
            content = self.getItemOfObj( obj, xref, "Length" ) 
            if ( content == "" ):    #  说明没有找到Length项， 出错了
                print( "CMAP:" + obj + ":Error 3, no ToUnicode Length" )
                return                            # 继续处理后面的CMAP
            
            len1 = int( content.split(" ")[1] )    # 取7645 数字， 也就是字节流长度
            buf = self.file_tools.readLine()                        # 跳过 stream\r\n
            buf, len1 = self.file_tools.read( len1 )  # 由于通过 getItemOfObj(), 内存文件 正好定位到stream 的起始位置
            if ( obj == "51134") :
                print( "pos=%d; l=%d; len=%d, stream=" % ( self.file_tools.getPosition(),l, len1 ) )
                print( buf )
            
            # OK， 现在 buf 中的字节流就是steam 的内容， 下面进行解压, 解压后的内容存放在desbuf
            desbuf = ''
            desFile =  "f:/F_t_tmp/cmap/"+obj+"_stream.txt"
            desbuf = self.decompress( buf, len1, desbuf, desFile )

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
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        if ( obj == "50580"):
                            print( "读取的一行为:" + tmpbuf )
                        
                        keys = tmpbuf.split(" ")            # 这儿是重复利用keys变量，拆分编码
                        cmap[ keys[0][1:5] ] = int( keys[1][1:5], 16 )
                        if ( obj == "50580") :
                            #println "-------" + tmpbuf + "*&*&("+keys[0].substring(1,5)+")" + keys[1].substring(1,5)
                            print('obj == "50580"')
                        
                    
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
                                cmap[ str("%04X", key ) ] = value 
                            
                        else:       # 如果没有方括号，表示是连续性的
                            mapstart = int( keys[2][1:5], 16)   # mapstart编码的起始位
                            for j in range(0, rangelen ):
                                key = codestart + j
                                value = mapstart + j
                                # 2016.04.16          value 不用字符串格式， 直接用16进制值，便于后面解码
                                # 放弃这种方法， 直接用上面的字符串之前 加 \\u 来组建Unicode字符串， 然后转换即可
                                # 这样的话就不用进行字节操作， 不用关心内存的申请了
                                # 2016.04.25  仍然使用数值， 因为解码的时候使用数值更方便
                                cmap[ str("%04X", key ) ] = value 
                            
        except:
            print( " procType0Stream() 出错了3333 ..." )

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
        desbuf = zlib.decompress( srcbuf )
        with open( desFile, "wb" ) as fs:
            fs.write(desbuf)
        return desbuf
      

    '''
    /*
     * 14. processPage()
     *      处理指定页， 获得其内容，存放在指定文件中 (调试过程中需要存放在文件中, 正式使用只需要在内存中)
     * 入口参数
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
    def processPage( self, PageNo, pages, xref, cmaps, cmaplist, contentMap, desFile ):
        try :
            cmap = {}
            desbuf = ''
            
            buf = cmaplist[pages[PageNo]]      # 该页面用到的CMAP, 有可能为空, 即全英文文档
            #print( "第" +PageNo+"页("+pages[PageNo]+")--cmap对象有:" + buf + ":" )
            
            if ( buf != ""):   # 有cmap
                tmp = buf.split(" ")
                for item in tmp:        # 遍历该页面使用道德所有的cmap, 将其合并为一个哈希表
                    cmap.update( cmaps[item] )    # dict 相加, 如果有重复内容, 由后面的内容替代前面的
                
            # 获取内容对象, 有可能是多个
            buf = contentMap[ pages[PageNo] ]
            #print( "第" +PageNo+"页--内容对象有" + buf )
            tmp = buf.split(" ")        # 有可能是多个内容对象
            # 每个内容对象的描述信息类似于(51134的对象描述), <</Filter/FlateDecode/Length 1117>>stream
            for i in range( 0, len(tmp) ): 
                obj = tmp[i]
                buf = self.getItemOfObj( obj, xref, "Length" )        # 获取该内容对象的字节流长度
                if ( buf == "" ) :   # 如果获取长度失败, 说明文件已经被破坏
                    print( "第"+PageNo+"页已经被破坏 (1)" )
                    return

                len1 = int( buf.split(" ")[1] )    # 取7645 数字， 也就是字节流长度

                self.file_tools.readLine()         # 跳过 stream\r\n 这一行非数据
                buffer, len1 = self.file_tools.read( len1 )    # 由于通过 getItemOfObj(), 内存文件 正好定位到stream 的起始位置, 注意返回的是2个参数

                # OK， 现在 buffer 中的字节流就是steam 的内容， 下面进行解压, 解压后的内容存放在desbuf
                desfile = "F:/F_t_tmp/tmp1/"+PageNo+"_"+obj+"_stream.txt"
                desbuf = self.decompress( buffer, len1, desbuf, desfile )

                # 如果有cmap, 那么需要对desbuf进行解码, 否则就进行格式调整.
                
                '''
                desFile = "e:/t_tmp/page/" +obj + ".dat"

                RandomAccessFile wd = new RandomAccessFile( desFile, "rwd" )
                wd.write( desbuf, 0, desbuf.size() )
                wd.close()
                
                '''
                # 下面开始解码, 无需判断是否cmap 为null 或空， 如果解压后的内容有<>, 必然需要解码
                desFile = "F:/F_t_tmp/tmp1/" +obj + "_decode.dat"
                self.decode( desbuf, cmap, desFile )
            
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
     * depends on:
     *        file_tools.initStreamBuf(), .readLineST( streambuf)
     *        self.processBT(), .processBDC()
     */
    '''
    def decode( self, buf, cmap, desfile ) :
        try :
            streambuf = {}
            self.file_tools.initStreamBuf( buf , streambuf )
            
            # 字体大小对应的长度, Ps(px):磅(pt), 这个暂时用不上, 但是保留, 也许以后有用
            fontsize = {"5":5.3,    "5.5":5.9,  "6.5":7.0,  "7.5":8.0,  "9":9.6,
                            "10.5":11.2,"12":12.8,  "14":15.0,  "15":16.0,  "16":17.1,
                            "18":19.3,  "22":23.5,  "24": 25.7, "26": 27.8, "36":38.5,
                            "42":44.9}
            
            print( "#############===============" )
            #print( cmap )
            print( "#############===============" )
            
            pre_cell, cur_cell  = {}, {}       # 哈希表, 记录表格的单元格的位置信息, x, y, w, h
            pre_xy, cur_xy      = {}, {}       # 哈希表, 记录坐标的位置信息, x, y
            retbuf = ""
            cellMap, textMap, textIndexMap = {}, {}, {}
            print(desfile)
            
            while ( True ):
                tmpbuf = self.file_tools.readLineST( streambuf )
                if ( not tmpbuf ):
                    break
                tmpbuf = tmpbuf.decode("utf-8").strip()
                #print("================decode():readLineST()="+ tmpbuf)
                    
                print(tmpbuf)
                if ( "BT" in tmpbuf ):     # 如果是 包含"BT"/"ET"
                    print("decode():self.processBT():" + tmpbuf)
                    retbuf += self.processBT( tmpbuf, streambuf, cmap, pre_cell, cur_cell, pre_xy, cur_xy, textMap, cellMap, textIndexMap )
                    #println "BT->" + retbuf
                    
                if ( "BDC" in tmpbuf ) :     # 如果是 包含"BDC"/"EMC"   
                    print("decode():self.processBDC():" + tmpbuf)
                    retbuf += self.processBDC( tmpbuf, streambuf, cmap, pre_cell, cur_cell, pre_xy, cur_xy, textMap, cellMap, textIndexMap )
                    #println "BDC->" + retbuf

                # re 的处理应该在BT/ET, BDC/EDC 之外, 也就是单元格.
                if ( "re" in tmpbuf ) :     # 如果是 包含"BDC"/"EMC"   
                    print("decode():self.processBDC():" + tmpbuf)
                    self.processRE( tmpbuf, cur_xy, cur_cell, cellMap )

                #print("decode()!!!" + retbuf)
            with open( desfile, "w") as fs:
                #print( "==解码后的数据为==" )
                #print( retbuf )
                fs.write( retbuf )
            print("decode()!!!after write to file" )

            #dd = {}
            #for item in sorted( cellMap.items(), key=lambda d:d[0]):

            del(cellMap[1])
                
            print( sorted( cellMap.items(), key=lambda d:d[0]) ) # 按键值进行排序
            print( sorted( textIndexMap.items(), key=lambda d:d[0]) )
            print("=======================================")
            print( sorted( textMap.items(), key=lambda d:d[0]) ) # 按键值进行排序

            for key,value in sorted( textIndexMap.items(), key=lambda d:d[0] ):
                print( value + ":" + textMap[value] )

            # 创建cellIndexMap, 存放 单元格对应的txt信息, {单元格编号:文本编号,}
            cellIndexMap = {}
            for k,v in sorted( cellMap.items(), key=lambda d:d[0]):
                cx, cy, cw, ch = v[0],v[1],v[2],v[3]      # 表格的x,y,w,h
                #下面轮循察看所有的txt 坐标, 如果有坐标在cell中, 就把该cell编号(key)与txt
                # 编号添加到cellIndexMap中
                alist = []
                for k1,v1 in sorted( textIndexMap.items(), key=lambda d:d[0]) :
                    xy = v1.split(":")[1].split(",")
                    x,y = float(xy[0]), float(xy[1])
                    if ( cx <= x and x <= cx+cw and cy<=y and y <= cy+ch ):
                        alist.append(k1)
                    else:
                        if ( k1 == 48 ):
                            print("文本编号:%d(x,y)=(%.3f,%.3f):%s\r\n表格编号:%d(%.3f,%.3f,%.3f,%.3f)----" % (k1,x,y, textMap[v1], k, cx,cy,cw,ch) )
                cellIndexMap[k] = alist
            print(cellIndexMap)
                
        #except Exception as e:
        except:
            #t,v,tb = sys.exc_info()
            #print(t,v)
            traceback.print_exc()
            print( "decode() Exception Error!" )
            #print(repr(e))

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
    def processBT( self, buf, streambuf, cmap, pre_cell, cur_cell, pre_xy, cur_xy, textMap, cellMap, textIndexMap ):
        try :

            retbuf = ""
            tmpbuf = buf
            while ( True ):
                if ( not tmpbuf ):
                    break
                print("tmpbuf="+tmpbuf)
                # 1. 过滤 页眉，页脚， 水印
                #    判断是否包含  /Artifact && （/Top   /Bottom   /watermark）任一 
                #     如果包含， 则过滤后面的BDC, EMC 之间的内容  
                if ( ( "/Top" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) : 
                    # 页眉  , BDC 是起始标识
                    tmpbuf = self.file_tools.readLineST( streambuf )
                    while ( tmpbuf ):
                        if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                            break
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                    
                elif ( ( "/Bottom" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) : 
                    # 页眉  , BDC 是起始标识
                    while ( True ):     # 下面的循环判断比上面的循环判断可读性要高一点
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        if ( not tmpbuf ):
                            break
                        if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                            break
                    
                elif ( "BDC" in buf ):      # 一段文字  处理 BDC/EMC  文字部分
                    retbuf += self.processBDC( tmpbuf, streambuf, cmap, pre_cell, cur_cell, pre_xy, cur_xy, textMap, cellMap, textIndexMap ) # 调用 BT 的处理
                elif ( "re" in buf ):       # 58.08 323.96 124.82 19.02 re
                    # 如果 有 re 信息， 表示是表格, 获取cell 信息, 如果碰到Tm, 会置cur_cell=[:]
                    self.processRE( tmpbuf, cur_xy, cur_cell, cellMap )
                
                # 如有有q 信息, 那么表示保存当前的图形状态信息, 包括坐标信息, 然后到Q 再恢复
                #/* 暂时不处理q/Q, 因为re 使用的是绝对坐标
                #if ( "q" in buf ) :    # q
                #    self.processQ( streambuf )
                #}
                #*/
               
                # 处理字体信息, 如果需要显示的话, 需要根据字体以及x坐标来计算空格位置
                if ( "Tf" in tmpbuf ) :
                    # processTf()
                    ttt = 1    # 无用语句暂时占用位置
                
                
                # 如果buf 有 文本位置信息, 则处理后获得当前的xy 坐标
                if ( self.hasTxtPosition( tmpbuf ) ) :
                    self.processTxtPosition( tmpbuf, pre_xy, cur_xy, pre_cell, cur_cell )
                
                
                # 如果buf 有文本信息
                if ( self.hasText( tmpbuf ) ) :
                    retbuf += self.processText( tmpbuf, cmap, cur_xy, pre_xy, cur_cell, pre_cell, textMap, textIndexMap )
                

                if ( "ET" in tmpbuf ):  # 正文结束的标识
                    return retbuf
                    
                tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")   
            
        except:
            print( "processBT() Exception Error! 出错了:" )
            traceback.print_exc()

        return retbuf

    # textMap = {编号:[[坐标],[绝对坐标],'txt',[转换坐标tm]]}
    # cellMap = {编号:[x,y,w,h]}
    # tm = [a, b, c, d, e, f]    # 一直存放的是最新的tm数据
    def processBT1( self, buf, streambuf, cmap, textMap, cellMap, tm ):
        try :

            retbuf = ""
            tmpbuf = buf
            while ( True ):
                if ( not tmpbuf ):
                    break
                print("tmpbuf="+tmpbuf)
                # 1. 过滤 页眉，页脚， 水印
                #    判断是否包含  /Artifact && （/Top   /Bottom   /watermark）任一 
                #     如果包含， 则过滤后面的BDC, EMC 之间的内容  
                if ( ( "/Top" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) : 
                    # 页眉  , BDC 是起始标识
                    tmpbuf = self.file_tools.readLineST( streambuf )
                    while ( tmpbuf ):
                        if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                            break
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                    
                elif ( ( "/Bottom" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) : 
                    # 页眉  , BDC 是起始标识
                    while ( True ):     # 下面的循环判断比上面的循环判断可读性要高一点
                        tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")
                        if ( not tmpbuf ):
                            break
                        if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                            break
                    
                elif ( "BDC" in buf ):      # 一段文字  处理 BDC/EMC  文字部分
                    retbuf += self.processBDC1( tmpbuf, streambuf, cmap, textMap, cellMap, tm ) # 调用 BT 的处理
                elif ( "re" in buf ):       # 58.08 323.96 124.82 19.02 re
                    # 如果 有 re 信息， 表示是表格, 获取cell 信息, 如果碰到Tm, 会置cur_cell=[:]
                    self.processRE1( tmpbuf, cellMap )
                
                # 如有有q 信息, 那么表示保存当前的图形状态信息, 包括坐标信息, 然后到Q 再恢复
                #/* 暂时不处理q/Q, 因为re 使用的是绝对坐标
                #if ( "q" in buf ) :    # q
                #    self.processQ( streambuf )
                #}
                #*/
               
                # 处理字体信息, 如果需要显示的话, 需要根据字体以及x坐标来计算空格位置
                if ( "Tf" in tmpbuf ) :
                    # processTf()
                    ttt = 1    # 无用语句暂时占用位置
                
                
                # 如果buf 有 文本位置信息, 则处理后获得当前的xy 坐标
                if ( self.hasTxtPosition( tmpbuf ) ) :
                    self.processTxtPosition1( tmpbuf, textMap, cellMap, tm  )
                
                
                # 如果buf 有文本信息
                if ( self.hasText( tmpbuf ) ) :
                    retbuf += self.processText1( tmpbuf, cmap, textMap, cellMap, tm  )
                

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
     *       self.processBDC(), .processRE(), /*processQ()*/
     *       self.hasTxtPosition(), .processTxtPosition(),  .hasText(), .processText(),
     *       self.file_tools.readLineST()
     * 
     */
    '''
    def processBDC( buf, streambuf, cmap, pre_cell, cur_cell, pre_xy, cur_xy, textMap, cellMap, textIndexMap ) :
        try:
            retbuf = ""
            tmpbuf = buf
            while ( True ) :       
                # 1. 过滤 页眉，页脚， 水印
                #    判断是否包含  /Artifact && （/Top   /Bottom   /watermark）任一 
                #     如果包含， 则过滤后面的BDC, EMC 之间的内容  
                if ( ( "/Top" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ): 
                    # 页眉  , BDC 是起始标识
                    while ( True ):
                        tmpbuf = self.file_tools.readLineST( streambuf )
                        if ( not tmpbuf):
                            break
                        if ( "EMC" in tmpbuf.decode("utf-8") ):  # 页眉结束的标识
                            break
                    
                elif ( ( "/Bottom" in tmpbuf ) and ( "/Pagination" in tmpbuf )  ) :
                    # 页眉  , BDC 是起始标识
                    while ( True ):
                        tmpbuf = self.file_tools.readLineST( streambuf )
                        if ( not tmpbuf):
                            break
                        if ( "EMC" in tmpbuf.decode("utf-8") ):  # 页眉结束的标识
                            break
                    
                elif ( "BT" in tmpbuf ) :    # 一段文字  处理 BDC/EMC  文字部分
                    retbuf += self.processBT( tmpbuf, streambuf, cmap, pre_cell, cur_cell, pre_xy, cur_xy, textMap, cellMap, textIndexMap ) # 调用 BT 的处理
                elif ( "re" in buf ) :    # 58.08 323.96 124.82 19.02 re
                    # 如果 有 re 信息， 表示是表格, 获取cell 信息, 如果碰到Tm, 会置cur_cell=[:]
                    self.processRE( tmpbuf, cur_xy, cur_cell, cellMap )
                
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
                    # processTf()
                    tttt = 1   # 无用语句暂时占用位置
                

                # 如果buf 有 文本位置信息, 则处理后获得当前的xy 坐标
                if ( self.hasTxtPosition( tmpbuf ) ):
                    print("????? 有位置信息？")
                    self.processTxtPosition( tmpbuf, pre_xy, cur_xy, pre_cell, cur_cell )
                    print(cur_xy)
                    print("++有位置信息+\r\n")
                
                
                # 如果buf 有文本信息
                if ( self.hasText( buf ) ) :
                    retbuf += self.processText( tmpbuf, cmap, cur_xy, pre_xy, cur_cell, pre_cell, textMap, textIndexMap )
                

                if ( "EMC" in tmpbuf ):  # 页眉结束的标识
                    return retbuf
                    
                tmpbuf = self.file_tools.readLineST( streambuf ).decode("utf-8")    
            
        except:
            print( "processBDC() Exception errlr!出错了:")
        
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
     * depends on:
     *       self.ifCRLF(), .processTj(), .processTJ()
     *          
     */
    '''
    def processText( self, buf, cmap, cur_xy, pre_xy, cur_cell, pre_cell, textMap, textIndexMap ) :
        retbuf = ""
        
        # 1. 判断是否需要换行
        print( "processText() begin:" + buf +":" )
        
        if ( self.ifCRLF1( pre_xy, cur_xy, pre_cell, cur_cell ) ) :
            retbuf += "\r\n"

        
        # 2. 解码
        if ( "Tj" in buf ) :                        # Tj
            retbuf += self.processTj( buf, cmap )
        elif ( "TJ" in buf ) :                      # TJ
            retbuf += self.processTJ( buf, cmap )
        elif ( "\'" in buf ) :                      # '   单引号, 等同于T*  Tj 也就是移到下一行起始位置输出文本
            retbuf += "\r\n" + self.processTj( buf, cmap )
        elif ( "\"" in buf ) :                      # "   双引号,  使用了字间隔与字符间隔, 内容而言与单引号一样
            retbuf += "\r\n" + self.processTj( buf, cmap )
        
        print( "processText() end:" + retbuf + ":" )
        print(cur_xy)

        key = str(len(textMap)+1)+":"+str(round( cur_xy['x']+cur_xy['ox'],3)) + ','+ str(round(cur_xy['y']+cur_xy['oy'] ,3) )

        textMap[key] = retbuf

        key1 = len(textIndexMap)+1
        textIndexMap[key1] = key

        with open(self.tmpfile1, "a+") as fs:
            fs.write("--------------------\r\n")
            fs.write( buf+"\r\n")
            fs.write( key + ":"+retbuf+"\r\n")
        
        return retbuf
    

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
        if ( "(" in buf ):                              # 不需要解码
            p1, p2 = buf.index('('),  buf.index(')')    # 获取'(' , ')' 的位置
            retbuf = buf[ p1+1 : p2 ].strip()           # 取小括号()中的内容
        elif ( "<" in buf ) :                           # 表示需要解码
            reg = re.compile(r'(<.+?>)')        # 需要解码的文本信息的正则表达式
            l = re.findall( reg, buf )          # 返回结果是各List, 以下同
            #print(" processTj()需要解码的文本数量%d" % len(l) )
            tmpbuf = ""
            for item in l:                      #  逐条获取不需要解码的文本信息
                tmpbuf += item[1:5]

            #print( "processTj() <>内的内容为:" + tmpbuf )
            for i in range(0, len(tmpbuf) // 4 ): 
                retbuf += chr( cmap[ tmpbuf[ i*4:(i+1) * 4 ] ] )

        print( "processTj() 解码后:" + retbuf + ":" )
        
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
     */
    '''
    def processTJ( self, buf, cmap ):
        print( "\r\nprocessTJ()" + buf )
        if ( "(" in buf and  "<" in buf ):        #  既包含非汉字， 也包含汉字编码
            # 这种情况不知道有没有, 暂时列在这儿， 不处理, 目前没有发现这种情况出现
            print( buf + "===============================既包含<>,有包含()的TJ \r\n" )
        elif ( "(" in buf ) :                   # 不需要解码
            reg = re.compile(r'(\(.+?\))')      # 不需要解码的文本信息的正则表达式
            l = re.findall( reg, buf )          # 返回结果是各List, 以下同

            #print(" processTJ() 不需要解码的文本数量%d" % len(l) )
            retbuf = ""
            for item in l:                      #  逐条获取不需要解码的文本信息
                retbuf += item
        elif ( "<" in buf ) :                   # 包含 < > 表示需要解码成unicode
            # 先将所有需要解码的编码合并在一起, 然后一起处理
            reg = re.compile(r'(<.+?>)')        # 需要解码的文本信息的正则表达式
            l = re.findall( reg, buf )          # 返回结果是各List, 以下同

            #print(" processTJ() 需要解码的文本数量%d" % len(l) )
            tmpbuf = ""
            for item in l:                      #  逐条获取不需要解码的文本信息
                tmpbuf += item[1:5]

            #print( "processTJ() <>内的内容为:" + tmpbuf )
            for i in range(0, len(tmpbuf) // 4 ): 
                retbuf += chr( cmap[ tmpbuf[ i*4, (i+1) * 4 ] ] )
            
        
        print( "processTJ() 解码后:" + retbuf + ":" )

        return retbuf
    

    '''
    /*
     * 22. ifCRLF( pre_xy, cur_xy, pre_cell, cur_cell ) 
     *      判断坐标信息, 包括单元格信息, 来判断是否需要
     *      只有处理文本的之前才需要判断是否要换行.
     * 入口参数
     *      
     * 出口参数
     *      
     * 返回值
     *      
     * 说明:
     *   1. 这儿不但要判断是否需要换行, 判断后还需要把 cur_cell, pre_cell, pre_xy 等哈希表
     *      进行重置, 否则后续判断可能会出错
     *   2. 如果有表格, 得判断该表格与上一次pre_xy 是否在同一行, 判断结束后, 要将上一次pre_xy 置空。
     *      因为后续的表格判断是否换行, 应该是依据 pre_cell
     *   3. 如何判断单元格内部的换行与第一个单元格与上一行的换行？？？
     *   4. 每个记录坐标的哈希表应该记录第一个绝对坐标, 也就是第一个Tm的x,y坐标, 后面的坐标都是相对坐标, 
     *      直到碰到下一个Tm坐标。
     *   5. cur_xy, pre_xy 的哈希表包含以下元素
     *      "x", "y", "OPR", "ox", "oy", 其中"ox", "oy" 是matrics coordinary 坐标.  如果x, y 本身就是绝对坐标, ox,oy就是0，0
     *      每次获取x,y坐标的时候， 要判断pre_xy["OPR"] 是否是Tm, re, Td/TD等， 来确定如何获取"ox","oy"
     *   6. 判断过程
     *      a. 如果cur_cell 不为空, 说明当前处理的文字在单元格内. 如果单元格内有分行正文, 
     *          每行正文之前都会用re重画单元格， 这样可以保证处理正文后置空的cur_cell又有位置信息了.
     *      b.

     * x  y  width height  re     画一个矩形. x,y 是左下角坐标, 
     */
    '''
    def ifCRLF1( self, pre_xy, cur_xy, pre_cell, cur_cell ) :
        retflag = False

        print("pre_xy, cur_xy, pre_cell, cur_cell---begin")
        print(pre_xy)
        print(cur_xy)
        print(pre_cell)
        print(cur_cell)
        print("-------------end--")
        try :
            # 1. 先判断pre_xy["OPR"]是否有, 如果没有说明这是第一个坐标, 也就是绝对坐标, 不用换行
            if ( "OPR" not in pre_xy.keys() ) :
                return False
            else :    # 如果不是第一行
                # 2. 如果上一次坐标记录是Tm, 本次是Td, 则是相对坐标, 判断 cur_xy["y"]是否等于0, 本次如果是re, 则 y 也不应该为0
                if ( pre_xy["OPR"] == "Tm" ) :              # 上一次是Tm, 则后续y 不等于 0 都换行
                    if ( cur_xy["y"] == 0 ) :
                        return False        
                    else :
                        return True
                    
                elif ( pre_xy["OPR"] == "re" ) :            #上一次位置操作是re
                    # 3. 如果上一次操作是 re, 本次是Td, 则是绝对坐标, 直接判断cur_xy 是否在 cur_cell的范围内
                    # 这种情况就是先判断 单元格是否需要换行, 再判断内容是否在单元格内, 
                    if ( cur_xy["OPR"] == "Td" or cur_xy["OPR"] == "TD" or cur_xy["OPR"] == "Tm"  ) :
                        if ( pre_xy["y"] >= cur_cell["y"] and pre_xy["y"] <= cur_cell["y"] + cur_cell["h"] ) :   # 这种情况极少, 即前一次处理的文本的Y坐标在本次单元格Y坐标范围内
                            retflag = False 
                        else:
                            retflag = True
                    
                    if ( cur_xy["OPR"] == "Td" or cur_xy["OPR"] == "TD" ) :
                        tttt = 1
                    
                    if ( len( cur_cell ) > 0 ) :        # 当前处理是单元格
                        if ( len( pre_cell ) > 0 ) :    # 上一次处理也是单元格
                            # 判断2个单元格的Y坐标
                            if ( cur_cell["y"] == pre_cell["y"] ) :
                                retflag = False
                            else :
                                retflag = True
                            
                        else :        # 上一次处理不是单元格
                            # 下面的判断是表格的第一个单元格与之前的文字位置比较
                            ttttt = 1

                    else :          # 2. 当前处理不是单元格, cur_xy 与 pre_xy 进行判断
                        if ( len( pre_xy ) > 0 ) :     # 有最后一次处理的坐标, 那么这儿就是判断相对坐标
                            if ( cur_xy["y"] == 0 or cur_xy["y"] == pre_xy["y"] ) :   # 有时候是绝对坐标
                                retflag = False         # 不用换行
                            else :
                                retflag = True          # 需要换行
                            
                        else :
                            retflag = True             # 需要换行, 由于后续处理Tm 等会重置pre_xy为空, 所以这儿缺省也是需要换行
                        
                

                # 4. 如果上一次操作是 Td/TD, 则是相对坐标, 直接判断cur_xy["y"]是否等于pre_xy["y"]
             
            # 5. 最后重置 pre_xy, pre_cell, 哈希表直接赋值不行， 函数外部没有改变出口参数的内容
            #    不应该重制 pre_cell 与 cur_cell, 这2个应该只在 RE 中进行修改.???????????
            pre_xy = cur_xy.copy()
            
        except:
            print( "ifCRLF1() Exception Error!")
            traceback.print_exc()
        
        return retflag
    
    
    def ifCRLF( self, pre_xy, cur_xy, pre_cell, cur_cell ) :
        retflag = False

        if ( len( cur_xy ) == 0 ):          # 这种情况其实是错误了, 处理文字的时候不可能没有坐标, 这儿的判断是为了容错处理
            return False
        
        # 1. 先判断有单元格的情况
        if ( len( cur_cell ) > 0 ):         # 有单元格
            # 先判断当前文字Y坐标是否在单元格内, 如果不在, 直接换行， 不进行后续判断
            # 有等号条件是因为文字如果在表格线上的话, 也换行(这种情况几乎没有, 容错而已)
            absY = cur_xy["y"] + cur_xy["oy"]   # y绝对坐标值
            if ( absY <= cur_cell["y"] and absY >= cur_cell["y"] + cur_cell["h"] ) :
                # 这种情况极少, 即前一次处理的文本的Y坐标在本次单元格Y坐标范围内
                return True
            
            elif ( len( pre_cell ) > 0 ) :  # 上一次处理也是单元格
                # 判断2个单元格的Y坐标
                if ( cur_cell["y"] == pre_cell["y"] ) :     # 同一个单元格，可能有多行文字
                    retflag = False
                else :
                    retflag = True
                
            else :        # 上一次处理不是单元格， 判断当前单元格与之前的文字是否在同一行
                # 下面的判断是表格的第一个单元格与之前的文字位置比较
                absY =  pre_xy["y"] + pre_xy["oy"]
                if ( absY > cur_cell["y"] and absY < cur_cell["y"] + cur_cell["h"] ) :
                    retflag = False 
                else:
                    retflag = True
            
        else:                           # 2. 没有单元格, cur_xy 与 pre_xy 进行判断 
            if ( len( pre_xy ) > 0 ) :      # 有最后一次处理的坐标, 那么这儿就是判断相对坐标
                if ( ( cur_xy["y"] + cur_xy["oy"] ) == ( pre_xy["y"] + pre_xy["oy"] ) ) : 
                    retflag = False         # 不用换行
                else :
                    retflag = True          # 需要换行
                
            else :                          # 这种情况是整个页的第一行, 而且不是表格的单元格内
                retflag = True              # 需要换行
         
        
        # 3. 最后重置 pre_xy, pre_cell, 哈希表直接赋值不行， 函数外部没有改变出口参数的内容
        pre_xy = cur_xy
        pre_cell = cur_cell
        
        cur_xy, cur_cell = {}, {}
        
        return retflag          #
    
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
     *
     */
    '''
    def processRE( self, buf, cur_xy, cur_cell, cellMap ) :
        try :
            print("+++++++++processRE() being+++++++++" + buf)
            tmpbuf = buf.split(" ")
            for i in range( 0, len(tmpbuf) ): 
                if ( "re" in tmpbuf[i] ) :              # 如果找到re, 那么前面i-4, i-3, i-2, i-1就是x,y,w,h
                    cur_cell["x"] = float( tmpbuf[i-4] )
                    cur_cell["y"] = float( tmpbuf[i-3] )
                    cur_cell["w"] = float( tmpbuf[i-2] )
                    cur_cell["h"] = float( tmpbuf[i-1] )
                    # 对于OPR== re 的cur_xy, (x,y)= (0,0) (ox,oy)=(0,0), 相当于特殊处理, 这样后续的坐标比较就不用特殊处理了
                    cur_xy["OPR"] = "re"

                    if ( cur_cell["x"] < 0 or cur_cell["h"] < 1 or cur_cell["w"] < 1 ):
                        continue
                    key = len(cellMap)+1     #str(len(cellMap)+1)
                    value = [ cur_cell["x"], cur_cell["y"], cur_cell["w"], cur_cell["h"] ]
                    if ( value not in cellMap.values() ):
                        cellMap[key] = value

                    with open("F:/F_T_tmp/tmp1/re.txt","a+") as fs:
                        fs.write( "buf=%s,re: x=%d,y=%d,w=%d,h=%d\r\n" % ( buf,cur_cell["x"],cur_cell["y"],cur_cell["w"],cur_cell["h"] ))

                    return
            
        except:
            print( "processRE() Exception error:" )
            return

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
        print("\r\nhasTxtPosition():" + buf)
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
    def processTxtPosition( self, buf, pre_xy, cur_xy, pre_cell, cur_cell ) :
        print("processTxtPosition():" + buf)
        if ( "Td" in buf ) :
            self.processTd( buf, pre_xy, cur_xy, pre_cell, cur_cell )
            return
        
        if ( "TD" in buf ) :
            self.processTD( buf, pre_xy, cur_xy, pre_cell, cur_cell )
            return
        
        if ( "Tm" in buf ) :
            self.processTm( buf, cur_xy, pre_xy, pre_cell, cur_cell )
            print("processTxtPosition()---- after processTM()")
            print(cur_xy)
            print(pre_xy)
            return
        
        if ( "T*" in buf ) :
            self.processTstar( buf, cur_xy, pre_cell, cur_cell )
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
     * depends on:
     *      self.getOriginXY()
     *   
     * 
     */
    '''
    def processTd( self, buf, pre_xy, cur_xy, pre_cell, cur_cell ) :
        try : 
            tmpbuf = buf.split(" ")
            pre_xy = cur_xy.copy()       # 将上一次的cur_xy 保存为 pre_xy
            
            for i in range( 0, len(tmpbuf) ): 
                if ( "Td" in tmpbuf[i] ) :     # 如果找到Td, 那么前面i-2, i-1就是x,y
                    cur_xy["x"] = float( tmpbuf[i-2] )
                    cur_xy["y"] = float( tmpbuf[i-1] )
                    cur_xy["OPR"] = "Td"
                    
                    self.getOriginXY( cur_xy, pre_xy )  # cur_xy["ox"], cur_xy["oy"]赋值
                    return
                
        except:
            print( "processTd() error:")
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
    def processTD( self, buf, pre_xy, cur_xy, pre_cell, cur_cell ) :
        try :
            tmpbuf = buf.split(" ")
            print(pre_xy)
            pre_xy = cur_xy.copy()       # 将上一次的cur_xy 保存为 pre_xy
            print("processTD()------------sss---------------")
            print(pre_xy)
            for i in range(0, len(tmpbuf) ):
                if ( "TD" in tmpbuf[i] ) :              # 如果找到TD, 那么前面i-2, i-1就是x,y
                    cur_xy["x"] = float( tmpbuf[i-2] )
                    cur_xy["y"] = float( tmpbuf[i-1] )
                    cur_xy["OPR"] = "TD"
                    
                    self.getOriginXY( cur_xy, pre_xy )  # cur_xy["ox"], cur_xy["oy"]赋值
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
     */
    '''
    def getOriginXY( self, cur_xy, pre_xy ) :
        try:
            print("getOriginXY():-----------------------------======================================")
            print(cur_xy)
            print(pre_xy)

            # 下面来获取ox, oy, 也就是参考坐标的原始坐标值(参照物), 如果x,y 本身就是绝对坐标,则ox,oy = 0,0
            if ( "OPR" not in pre_xy.keys() ) :      # 如果没有上一次的位置操作符, 说明是第一行, 则x,y 就是绝对坐标
                cur_xy["ox"] = 0
                cur_xy["oy"] = 0
            else :
                if ( pre_xy["OPR"] == "Td" or pre_xy["OPR"] == "TD" ) :  # 本次操作的参考坐标是上次操作的绝对坐标
                    cur_xy["ox"] = pre_xy["x"] + pre_xy["ox"]
                    cur_xy["oy"] = pre_xy["y"] + pre_xy["oy"]
                elif ( pre_xy["OPR"] == "T*" ) :       # 上次操作是T*
                    #println 这种情况没有碰到过, 不知道如何处理
                    # 一般T* 后面的位置操作符是Tm
                    TTTT = 12     # 无用语句占用位置, 未来处理, 暂缺.
                elif ( pre_xy["OPR"] == "re" ):  # 上次是个表格的单元格, 则本次肯定是绝对坐标
                    cur_xy["ox"] = 0
                    cur_xy["oy"] = 0
                elif ( pre_xy["OPR"] == "Tm" ) :  # Tm 的x,y 坐标就是本次的ox,oy
                    cur_xy["ox"] = pre_xy["x"]
                    cur_xy["oy"] = pre_xy["y"]
        except:
            print("getOriginXY() Exception Error!")
            traceback.print_exc()
            print(cur_xy)
            print(pre_xy)
            

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
     */
    '''
    def processTm( self, buf, cur_xy, pre_xy, pre_cell, cur_cell ) :
        try :
            print("===========================-------------------------processTm()" + buf)
            tmpbuf = buf.split(" ")
            print(tmpbuf)
            
            for i in range(0, len(tmpbuf) ):
                if ( "Tm" in tmpbuf[i] ) :              # 如果找到Tm, 那么前面i-2, i-1就是x,y
                    cur_xy["x"] = float( tmpbuf[i-2] )
                    cur_xy["y"] = float( tmpbuf[i-1] )
                    cur_xy["OPR"] = "Tm"
                    
                    cur_xy["ox"] = 0
                    cur_xy["oy"] = 0

                    pre_cell, cur_cell, pre_xy = {}, {}, {}

                    print("===========================-------------------------processTm()")
                    print( cur_xy )
                    return
            
        except:
            print( "processTm() error:" )
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
     * 
     */
    '''
    def processTstar( self, buf, cur_xy, pre_cell, cur_cell ) :
        try :
            tmpbuf = buf.split(" ")
            pre_xy = cur_xy.copy()       # 将上一次的cur_xy 保存为 pre_xy
            for i in range( 0, len(tmpbuf) ): 
                if ( "T*" in tmpbuf[i] ) :              # 如果找到T*, 那么前面i-2, i-1就是x,y
                    cur_xy["x"] = 0         
                    cur_xy["y"] = pre_xy["y"] - 1       # 设-1 表示与上次处理的位置相比, 下移了, 那么就是下一行
                    cur_xy["OPR"] = "T*"
                    
                    cur_xy["ox"] = pre_xy["x"]
                    cur_xy["oy"] = pre_xy["y"]
                    # 注意， 上面的操作是假设T* 不会是第一个位置操作符， 目前测试也
                    # 确实没有第一个的情况, 但是如果真有T*是第一个位置操作符, 就会出异常
                    # 因为这个时候pre_xy["x"]等访问是无效的。
                    return
                
            
        except:
            print( "processTstar() error:" )
            return


    
    
pdf = pdfService()

pdf.parsePDF('F:/F_T_tmp/1202.pdf')
