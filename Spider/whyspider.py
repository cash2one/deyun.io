
# -*- coding: utf-8 -*-
#---------------------------------------
#   程序：whyspider.py
#   版本：0.3
#   作者：why
#   修改：markselby
#   日期：2014-04-18
#   语言：Python 2.7.5
#
#   版本列表：
#   0.1：添加GET和POST
#   0.2：添加模拟头的功能
#   0.3: 添加正则表达式的处理，暂未完成
#---------------------------------------

import urllib  
import urllib2
import cookielib
import re
import string
# import bs4	#beautiful soup

class WhySpider:
    
    # 初始化爬虫  
    def __init__(self):
        """
        初始化函数，默认模拟电脑火狐浏览器登录
        """
        self.cookie_jar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
        self.headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0'}

    # 发送GET请求
    def send_get(self,get_url):
        """
        发送GET请求，参数为GET的URL
        """
        result = ""
        try:
            my_request = urllib2.Request(url = get_url, headers = self.headers)
            result = self.opener.open(my_request).read()
        except Exception,e:
            print "Exception : ",e
        return result

    # 发送POST请求
    def send_post(self,post_url,post_data):
        result = ""
        try:
            my_request = urllib2.Request(url = post_url,data = post_data, headers = self.headers)
            result = self.opener.open(my_request).read()
        except Exception,e:
            print "Exception : ",e
        return result

    # 模拟电脑
    def set_computer(self):
        user_agent = 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:28.0) Gecko/20100101 Firefox/28.0'
        self.headers = { 'User-Agent' : user_agent }    
        
    # 模拟手机
    def set_mobile(self):
        user_agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A403 Safari/8536.25'
        self.headers = { 'User-Agent' : user_agent }    

    # 初级爬虫，简单返回HTML
    def get_html(self, url):
	self.response = urllib2.Request(url)
	return self.opener.open(self.response).read() 

    # 判断是否可能url能匹配该正则表达式，适用于判断
    def re_exists(self, url, patternstr):
	self.content = self.get_html(url) 
	pattern = re.compile(patternstr)
	self.match = pattern.search(self.content)
	if self.match:
		return "Found!"
	else:
		return "Not found!"
	
    # 获取某个url里面所有符合正则表达式的结果，返回list
    def re_getall(self, url, patternstr):
	self.req = urllib2.Request(url)
	self.content = self.opener.open(self.req).read()
	# 可能需要beautifulsoup来处理中文，明天来修改
	pattern = re.compile(patternstr)
	match = pattern.findall(self.content)
	return match

    def re_getall2(self, url, patternstr):
	self.content = self.get_html(url)
	self.content = str(bs4.BeautifulSoup(self.content))
	#print self.content
	pattern = re.compile(patternstr)
	match = pattern.findall(self.content)
	return match	
