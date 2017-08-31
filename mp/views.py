# -*- coding: utf-8   -*-

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.views import generic

import hashlib

import time

# Create your views here.
def index( request ):
    
    signature   = request.GET.get('signature')
    timestamp   = request.GET.get('timestamp')
    nonce       = request.GET.get('nonce')
    echostr     = request.GET.get('echostr ')

    if ( not signature):
        signature = "signature"

    if ( not timestamp):
        timestamp = "timestamp"

    if ( not nonce):
        nonce = "nonce"

    if ( not echostr):
        echostr = "echostr"

    token = "rMoonSta1234oHello1234"
    print(" signature=%s, \r\n timestamp=%s, nonce=%s, echostr=%s" % (signature, timestamp, nonce, echostr ) )

    a1 = [ token, timestamp, nonce ]
    print(a1)

    a2 = sorted(a1)
    print(a2)

    tmp = ''.join(a2)
    print(tmp)
    buf = tmp.encode("utf-8")
    print(buf)

    sha = hashlib.sha1(buf) #或hashlib.md5()

    encrypts = sha.hexdigest() #生成40位(sha1)或32位(md5)的十六进制字符串
    print( encrypts )

    
    if ( encrypts == signature ):
        print("校验通过")
        return HttpResponse(echostr)
    else:
        print("校验失败!")
        return HttpResponse("False")
    
