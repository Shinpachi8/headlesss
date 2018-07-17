#!/usr/bin/env python
# coding=utf-8


import re
import json
import socket
import sys
import string
import urllib
import logging
import requests.packages.urllib3
from tldextract import extract, TLDExtract
import time
from hashlib import md5
try:
    import httplib
except:
    import http.client as httplib
import ssl
try:
    import urlparse
except:
    from urllib import parse as urlparse
import random
import requests
from requests import  ConnectTimeout
import argparse

STATIC_EXT = ["f4v","bmp","bz2","css","doc","eot","flv","gif"]
STATIC_EXT += ["gz","ico","jpeg","jpg","js","less","mp3", "mp4"]
STATIC_EXT += ["pdf","png","rar","rtf","swf","tar","tgz","txt","wav","woff","xml","zip"]
STATIC_EXT += ['a3c', 'ace', 'aif', 'aifc', 'aiff', 'arj', 'asf', 'asx', 'attach', 'au',
            'avi', 'bin', 'cab', 'cache', 'class', 'djv', 'djvu', 'dwg', 'es', 'esl',
            'exe', 'fif', 'fvi', 'gz', 'hqx', 'ice', 'ief', 'ifs', 'iso', 'jar', 'kar',
            'mid', 'midi', 'mov', 'movie', 'mp', 'mp2', 'mp3', 'mp4', 'mpeg',
            'mpeg2', 'mpg', 'mpg2', 'mpga', 'msi', 'pac', 'pdf', 'ppt', 'pptx', 'psd',
            'qt', 'ra', 'ram', 'rm', 'rpm', 'snd', 'svf', 'tar', 'tgz', 'tif',
            'tiff', 'tpl', 'uff', 'wav', 'wma', 'wmv', 'doc', 'docx', 'db', 'jpg']

BLACK_LIST_PATH = ['logout', 'log-out', 'log_out']


BLACK_LIST_HOST = ['safebrowsing.googleapis.com', 'shavar.services.mozilla.com',]
BLACK_LIST_HOST += ['detectportal.firefox.com', 'aus5.mozilla.org', 'incoming.telemetry.mozilla.org',]
BLACK_LIST_HOST += ['incoming.telemetry.mozilla.org', 'addons.g-fox.cn', 'offlintab.firefoxchina.cn',]
BLACK_LIST_HOST += ['services.addons.mozilla.org', 'g-fox.cn', 'addons.firefox.com.cn',]
BLACK_LIST_HOST += ['versioncheck-bg.addons.mozilla.org', 'firefox.settings.services.mozilla.com']
BLACK_LIST_HOST += ['blocklists.settings.services.mozilla.com', 'normandy.cdn.mozilla.net']
BLACK_LIST_HOST += ['activity-stream-icons.services.mozilla.com', 'ocsp.digicert.com']
BLACK_LIST_HOST += ['safebrowsing.clients.google.com', 'safebrowsing-cache.google.com', ]
# BLACK_LIST_HOST += ['127.0.0.1', 'localhost']

class TURL(object):
    """docstring for TURL"""
    def __init__(self, url):
        super(TURL, self).__init__()
        self.url = url
        self.format_url()
        self.parse_url()
        if ':' in self.netloc:
            tmp = self.netloc.split(':')
            self.host = tmp[0]
            self.port = int(tmp[1])
        else:
            self.host = self.netloc
            self.port = 80
        if self.start_no_scheme:
            self.scheme_type()

        self.final_url = ''
        self.url_string()

    def parse_url(self):
        parsed_url = urlparse.urlparse(self.url)
        self.scheme, self.netloc, self.path, self.params, self.query, self.fragment = parsed_url

    def format_url(self):
        if (not self.url.startswith('http://')) and (not self.url.startswith('https://')):
            self.url = 'http://' + self.url
            self.start_no_scheme = True
        else:
            self.start_no_scheme = False

    def scheme_type(self):
        if is_http(self.host, self.port) == 'http':
            self.scheme = 'http'

        if is_https(self.host, 443) == 'https':
            self.scheme = 'https'
            self.port = 443

    @property
    def get_host(self):
        return self.host

    @property
    def get_port(self):
        return self.port

    @property
    def get_scheme(self):
        return self.scheme

    @property
    def get_path(self):
        return self.path

    @property
    def get_query(self):
        """
        return query
        """
        return self.query

    @property
    def get_dict_query(self):
        """
        return the dict type query
        """
        return dict(urlparse.parse_qsl(self.query))

    @get_dict_query.setter
    def get_dict_query(self, dictvalue):
        if not isinstance(dictvalue, dict):
            raise Exception('query must be a dict object')
        else:
            self.query = urllib.urlencode(dictvalue)

    @property
    def get_filename(self):
        """
        return url filename
        """
        return self.path[self.path.rfind('/')+1:]

    @property
    def get_ext(self):
        """
        return ext file type
        """
        fname = self.get_filename
        ext = fname.split('.')[-1]
        if ext == fname:
            return ''
        else:
            return ext

    def is_ext_static(self):
        """
        judge if the ext in static file list
        """
        if self.get_ext in STATIC_EXT:
            return True
        else:
            return False

    def is_block_path(self):
        """
        judge if the path in black_list_path
        """
        for p in BLACK_LIST_PATH:
            if p in self.path:
                return True
        else:
            return False

    def is_block_host(self):
        """
        judge if the path in black_list_host
        """
        for p in BLACK_LIST_HOST:
            if p in self.host:
                return True
        else:
            return False

    def url_string(self):
        data = (self.scheme, self.netloc, self.path, self.params, self.query, self.fragment)
        url = urlparse.urlunparse(data)
        self.final_url = url
        return url

    def __str__(self):
        return self.final_url

    def __repr__(self):
        return '<TURL for %s>' % self.final_url

def LogUtil(path='/tmp/test.log', name='test', level='1'):
    levels = {
        '1': logging.INFO,
        '2': logging.WARNING,
        '3': logging.ERROR
    }
    logger = logging.getLogger()
    logger.setLevel(levels[level])

    #create formatter
    formatter = logging.Formatter(fmt=u'[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s ')

    # create console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # create file
    file_handler = logging.FileHandler(path, encoding='utf-8')
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


# logger = LogUtil()

def is_http(url, port=None):
    """
    judge if the url is http service
    :url  the host, like www.iqiyi.com, without scheme
    """
    if port is None: port = 80
    service = ''
    try:
        conn = httplib.HTTPConnection(url, port, timeout=10)
        conn.request('HEAD', '/')
        conn.close()
        service = 'http'
    except Exception as e:
        #print "[lib.common] [is_http] {}".format(repr(e))
        pass

    return service

def is_https(url, port=None):
    """
    judge if the url is https request
    :url  the host, like www.iqiyi.com, without scheme
    """
    ssl._create_default_https_context = ssl._create_unverified_context
    if port is None: port = 443
    service = ''
    try:
        conn = httplib.HTTPSConnection(url, port, timeout=10)
        conn.request('HEAD', '/')
        conn.close()
        service = 'https'
    except Exception as e:
        #print "[lib.common] [is_http] {}".format(repr(e))
        pass

    return service

def hashmd5(string):
    try:
        string = string.encode('utf-8')
    except:
        string = string
    return md5(string).hexdigest()


def get_basedomain(url, basedomain=1):
    try:
        if basedomain == 1:  # xxx.iqiyi.com
            return urlparse.urlparse(url).netloc
        elif basedomain == 2: # iqiyi.com
            return extract(url).registered_domain
        elif basedomain == 3: # iqiyi
            return extract(url).domain # 更加有关联性的处理方法
    except Exception as e:
        pass



def argsparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--basedomain", type=int, default=1, help="get the domian of url,i.e. url=www.iqiyi.com if value=1, return www.iqiyi.com, if value=2, return iqiyi.com, if value=3 return iqiyi")
    parser.add_argument("--limit", type=int, default=20, help="the time limit default 20m")
    parser.add_argument("-u", help="the url to spider")
    parser.add_argument("--taskname", default="test", help='the taskname wanna set')
    parser.add_argument("--goon", help="continue the spider")
    parser.add_argument("--wsaddr", help="the websocket address of headless chrome")
    args = parser.parse_args()
    if args.wsaddr is None or args.u is None:
        parser.print_help()
        sys.exit(-1)
    return args

if __name__ == '__main__':
    s = TURL('http://static.iqiyi.com/js/pingback/iwt.js?_=21312312')
    print(get_basedomain(str(s)))
    assert s.is_ext_static() == True
