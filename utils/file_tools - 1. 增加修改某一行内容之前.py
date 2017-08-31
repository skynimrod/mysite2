# -*-  coding: utf-8  -*-

# 文件操作工具

# 1. 向文件中插入目标内容
#    碰到有poskey 字符串才插入。 这是重点
#    注意: tmpfile 操作的是字节, 而 普通的文件操作时字符串...
import tempfile
import shutil
import time
import traceback
def insertContent( filename, contentstr, poskey ):
    temp = tempfile.TemporaryFile()
    fp = open( filename, 'r+' )
    print( temp.name )

    buf = ''
    flag = False
    try:
        while(True):
            buf = fp.readline()

            if ( not buf ) :  # 文件结束
                break

            print(buf)

            # 判断是否到了插入位置， flag 判断是为了只插入一次内容
            if (buf.find(poskey) != -1 and not flag ):  
                flag = True     # 表示找到了插入位置
                tbuf = contentstr + '\n'
                temp.write( tbuf.encode('utf-8') )

            temp.write( buf.encode('utf-8') )


        print('---------')
        temp.seek( 0 )    # 回到临时文件头部, 开始复制文件
        fp.seek(0)
        while(True):
            buf = temp.readline()    # temp 读出来的是字节流
            if ( not buf):   # 文件结束
                break
            fp.write(buf.decode('utf-8'))
            print(buf.decode('utf-8'))
        
        print('复制结束')
        '''
        #time.sleep( 1000 )
        os.remove( filename )
        shutil.copyfile( temp.name, filename )
        '''
    except IOError as err:
        print("Error:" + err)
    finally:
        fp.close()
        temp.close()
        print('finally')


# 0. 判断文件是否被打开
# http://www.cnblogs.com/plwang1990/p/5863560.html
from ctypes import cdll
import os

def is_open( filename ):
    _sopen = cdll.msvcrt._sopen
    _close = cdll.msvcrt._close
    _SH_DENYRW = 0x10

    if not os.access( filename, os.F_OK ):
        return False             # 文件不存在

    h = _sopen( filename, 0, _SH_DENYRW, 0 )
    if h == 3 :
        _close(h)
        return False             # 文件没有被任何人打开

    return True       # 文件已经被打开了


#filename = 'models.py'
#content = 'import shutil'

#insertContent( filename, content, 'import')
#print( is_open("url_tools.py") )
import datetime
class util_fileService(object):
    _bytestream = ''
    _readBuffer={}   # 三个元素: filename, position, buf, filelen, buflen

    def __init__(self):
        self.val = 1
        
    def initReadFileMap( self,srcFile ):
        print( "要处理的文件为:" + srcFile )
        self._readBuffer["filename"] = srcFile
        self._readBuffer["pos"]      = 0

        flen = os.path.getsize( srcFile )
        self._readBuffer["filelen"]  = flen
        self._readBuffer["buflen"]  = flen
        
        fp = open( srcFile, 'rb' )
        self._bytestream = fp.read(flen)
        fp.close()

        self._readBuffer["buf"] = self._bytestream

    # 内存映射文件的操作方法， 获取当前操作的文件名称    
    def getFileName(self):
        return self._readBuffer['filename']

    # 内存映射文件的操作方法， 获取当前操作的文件长度
    def getFileLength(self):
        return self._readBuffer["filelen"]
    
    # 内存映射文件的操作方法, 读取当前操作文件的一行, 并自动移动指针
    def readLine(self):
        curpos = self._readBuffer["pos"]

        if ( curpos >= self._readBuffer["buflen"] ):    # 如果到结尾或超出结尾位置， 返回空
            return ""
        
        timeStar = datetime.datetime.now() # 得到当前的时间

        for  i in range( curpos, self._readBuffer["buflen"]) :
            ch = self._readBuffer["buf"][i]
            if ( ch == 13 or ch == 10 ): # 找到换行回车了   13 = "\0x0D", 10 = "0x0A"
                # 先把\0A或\0D之前的数据获取出来
                tmp = self._readBuffer["buf"][curpos:i]
                # retbuf = tmp.decode('utf-8')   # 这儿不进行解码操作, 只有涉及到内容处理的时候才需要解码
                retbuf = tmp
                # 继续往后面找找， 如果是\0D 或 \0A 继续跳过
                          
                curpos = i      # curpos  赋值为当前的位置
                ch = self._readBuffer["buf"][curpos]

                while ( ch == 13 or ch == 10 ) :  # 继续跳过 后面的回车或换行
                    curpos += 1
                    ch = self._readBuffer["buf"][curpos]
                
                self._readBuffer["pos"] = curpos

                break
            
            
        
        timeEnd = datetime.datetime.now()  # 得到当前的时间  

        #if ( (timeEnd - timeStar) > 0 ) log.info "readLine() time :" + (timeEnd - timeStar) + "ms"
        return retbuf
    
    # 初始化一个字节流映射缓冲区，便于在该缓冲区上进行类似映射文件的存取操作
    def initStreamBuf( self,  stream , streambuf ):
        streambuf["buf"] = stream
        streambuf["pos"] = 0
        streambuf["buflen"] = len(stream)
        #print(streambuf)
    
    # 在指定的字节流上的操作方法, 读取一行, 并自动移动指针
    # readLineST( streambuf ) 
    # streambuf 是类似_readBuffer[] 哈希表的格式， 不过缺少文件信息， 仅仅是缓冲区信息
    def readLineST( self, streambuf ) :
        retbuf = ''
        try:
            curpos = streambuf["pos"]
            if ( curpos >= streambuf["buflen"] ) :    # 如果到结尾或超出结尾位置， 返回空
                #print("readLineST(), already arrived end!")
                return ""
            
            #print( "readLineST(),带参数的readLine" )
            timeStar = datetime.datetime.now() # 得到当前的时间

            retbuf = ''
            buflen = streambuf["buflen"]
            for  i in range( curpos, buflen ):
                ch = streambuf["buf"][i]
                if ( ch == 13 or ch == 10 or i >= buflen-1 ) :  # 找到换行回车了, 缓冲结束没有回车换行符
                    print(ch)
                    # 先把\0A或\0D之前的数据获取出来
                    tmp = streambuf["buf"][curpos:i]
                    #retbuf = tmp.decode('utf-8')
                    retbuf = tmp
                    # 继续往后面找找， 如果是\0D 或 \0A 继续跳过
                    curpos = i      # curpos  赋值为当前的位置
                    ch = streambuf["buf"][curpos]
                    while ( ch == 13 or ch == 10 ):  # 继续跳过 后面的回车或换行, 这儿也要判断是否到了缓冲区结束
                        curpos += 1 
                        if ( curpos >= streambuf["buflen"] ) :       # 说明到了内存缓冲区结束了
                            break
                        ch = streambuf["buf"][curpos]
                    
                    streambuf["pos"] = curpos
                    break
                
                
            timeEnd = datetime.datetime.now() # 得到当前的时间

            #if ( (timeEnd - timeStar) > 0 )
            #    log.info "readLine() time :" + (timeEnd - timeStar) + "ms"
        except :
            print("readLineST() Exception Error!")
            traceback.print_exc()
            
            print(streambuf)
        return retbuf
       
    '''
     * read() 类似  Java 文件操作的read() 功能， 读取一段字节流
     *    desBuf      目标要存储的空间
     *    start      起始位置缺省为-1, 表示从当前位置读取, 否则是指定的位置
     * 返回值:
     *      desBuf,rlen   返回2个参数:  字节流以及字节流的长度
     *      出错的返回的是  '', -1
    '''
    def read( self, length, start=-1 ):
        try:
            buflen = self._readBuffer["buflen"]
            rlen = length
            
            #print( "start=%d, len=%d, buflen=%d" % ( start, length, buflen ))
            if ( start > buflen ) :      # 如果越界就返回-1
                return '',-1

            # 起始位置的处理
            if ( start == -1 ):
                rpos = self.getPosition()
            else:
                self._readBuffer["pos"] = start 
                rpos = start
            
            #print( "start=%d(%08x), len=%d, buflen=%d" % ( rpos, rpos, length, buflen ))
            if ( ( rpos + length ) > buflen ) :
                rlen = buflen - start
            
            desBuf = self._readBuffer["buf"][rpos:rpos+rlen]
            self._readBuffer["pos"] = rpos + rlen  # 读取后修改当前的位置

            return desBuf,rlen
        except:
            print("read() Error!")
            return '',-1
        
    # getPosition() 获取当前内存映射文件或字节流中处理的位置
    def getPosition(self):
        return self._readBuffer["pos"] 
    
    
    # getPosition( streambuf ) 获取指定节流中处理的位置
    def getPositionST( streambuf ):
        return streambuf["pos"] 
    
    '''
     * seek() --  类似文件操作的定位功能， 不过这儿的定位很简单，就是修改缓冲区中的游标位置pos
     * 做了一些冗余， 定位如果是负数， 则从0开始 (这个未来可能会改变，即负数可以从后往前数)
     *    如果长度大于缓冲去长度(文件长度)，也就是定位到最后了
    '''
    def seek( self, pos ) :
        rpos = pos
        
        if ( pos < 0 ):
            rpos = 0
        
        if ( rpos >= self._readBuffer["buflen"] ):
            rpos = self._readBuffer["buflen"] -1   #下标是从0开始的， 所以要减1
        
        self._readBuffer["pos"] = rpos
    
    
    '''
     * seek() --  类似文件操作的定位功能， 不过这儿的定位很简单，就是修改缓冲区中的游标位置pos
     * 做了一些冗余， 定位如果是负数， 则从0开始 (这个未来可能会改变，即负数可以从后往前数)
     *    如果长度大于缓冲去长度(文件长度)，也就是定位到最后了
    '''
    def seekST( streambuf, pos ):
        rpos = pos
        
        if ( pos < 0 ):
            rpos = 0
        
        if ( rpos >= streambuf["buflen"] ):
            rpos = streambuf["buflen"] -1   #下标是从0开始的， 所以要减1
        
        streambuf["pos"] = rpos


def rlen( buf ):
    return int(( len(buf.encode("utf-8"))-len(buf) )/2 + len(buf) )  

import hashlib

signature   = "signature"
timestamp   = "timestamp"
nonce       = "nonce"
echostr     = "echostr"

token = "rMoonSta1234oHello1234"
print("signature=%s,timestamp=%s,nonce=%s,echostr=%s" % (signature, timestamp, nonce, echostr ) )

al = [ token, timestamp, nonce ]

print(al)
a2 = sorted(al)

print(a2)
tmp = ''.join(a2)
print(tmp)
buf = tmp.encode("utf-8")
print(buf)

sha = hashlib.sha1(buf) #或hashlib.md5()

encrypts = sha.hexdigest() #生成40位(sha1)或32位(md5)的十六进制字符串
print( encrypts )


sss = {'13': 'C2_1', '22': 'C2_2', '8': 'C2_0'}
print(sss)
for obj,fontname in sorted(sss.items(), key=lambda d:d[0]):
    del(sss[obj])

print(sss)
aaa = "   "
print(":%s:%d" % (aaa, len(aaa.strip()) ) )

flag1 = False
print(flag1)
flag1 = 1==1
print(flag1)


s1 = "比上年同期增长：83%—104%    "
s2 = "─────────────────────────────"
print(s1)
print(s2)
print(":%s:的长度为:%d" % (s1, rlen(s1)))
print("%s的长度为:%d" % (s2, rlen(s2)))
