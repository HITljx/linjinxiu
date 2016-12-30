#!/usr/bin/python
#encoding=utf-8

'''
Created on 2016/12/23
@author:Ljx

'''

'''
提取种子站点的一级目录和二级目录页面上的中文，提取关键字Top50：
1.爬虫(bs4)
 1.1连接数据库，读取种子站点
 1.2通过正则匹配把首页上所有的http链接都爬下来
 1.3筛选链接
    筛选规则：保留本域名的链接，去除含数字的链接

2.提取关键字
 2.1读取链接页面上的内容
 2.2通过正则匹配选取中文
 2.2导入LDA模型提取关键字Top50
 2.3把关键字插入到数据库中
'''
#import bs4  
#from bs4 import BeautifulSoup

import jieba
import jieba.analyse

import urllib
import urllib2

import re

import MySQLdb

#检测编码模块
import chardet
from chardet.universaldetector import UniversalDetector

from socket import error as SocketError

#errno系统符号
import errno

#用于在内存缓冲区中读写数据，类似于对文件的操作方法
import StringIO

import traceback

import time

#系统模块
import sys
reload(sys)
sys.setdefaultencoding('utf-8') 



#数据库信息
db_host = 'localhost'
db_username = 'root'
db_password = ''
db_database_name = 'freebuf_secpulse'
db_table_name = 'grabsite'

#设定结巴函数中提取关键字的数量topN
topK = 50


#函数：连接数据库
def getMysqlConn():
	return MySQLdb.connect(host = db_host,user = db_username,passwd = db_password,db = db_database_name,charset = "utf8")

#函数：数据库查询语句
def getSelectMysql():
	select_sql = "select siteDomain from " + db_table_name
	return select_sql
'''
#函数：插入到数据库
def insert_url():
	insert_sql = "insert into urls(siteDomain,url) "+"values(%s,%s)"
	return insert_sql

#函数：插入到数据库
def insert_tip():
	insert_sql = "insert into tips(siteDomain,tips) "+"values(%s,%s)"
	return insert_sql
'''
#函数：爬取所有的url
def spider_url(url):
	try:
		#抓取页面内容
		headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6' }
		req = urllib2.Request(url, headers = headers)
		html_1 = urllib2.urlopen(req).read()
		#输入html页面
		#print html_1

	except:
		pass
	
	#判断网站的编码方式，统一为utf-8编码
	encoding_dict =chardet.detect(html_1)
	web_encoding = encoding_dict['encoding']
	if web_encoding == 'utf-8' or web_encoding == 'UTF-8':
		html = html_1
		#print html
	else:
		html = html_1.decode('gbk','ignore').encode('utf-8')
		#print html

	#正则匹配http
	#re_http = re.compile(u"https?://.+?\s")
	re_http = re.compile(u"https?://[a-zA-Z0-9_-]+\..+?\"")
	res = re.findall(re_http, html)
	#输出页面所有的url
	#print res
	return res
	


#函数：url的筛选
def filter_url(get_url,domain):
	get_urls = []
	#筛选出含有本域名的url
	for url in get_url:
		if url.startswith(domain):

			#去除含有数字的url|(\.png\")
			re_url = re.compile(u"(\d+\.html\")|(\d+\.html#.+?\")|(\.gif\")|(\.png\")|(\.jpg\")|(\.jpng\")|(\.js\")|(\.css\")|(\.swf\")")
			res = re.findall(re_url, url)
			if res != []:
				continue
			get_urls.append(url)
			
	#输出过滤后的url
	#print get_urls
	return get_urls


#函数：爬取页面内容
def get_content(url):
	#抓取页面内容，缓存处理
	try:
		#包含头数据的字典
		headers = {'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6' }
		#地址创建一个request对象，通过调用urlopen并传入request对象，将返回一个相关请求response对象，这个应答对象如同一个文件对象，然后在Response中调用.read()。
		req = urllib2.Request(url, headers = headers)
		#返回一个response对象
		#response = urlli2.urlopen('url') 
		#response调用.read()
		#html = response.read()
		#html将两条代码合在一起
		html = urllib2.urlopen(req).read()
	except:
		#print "pass error"
		return 0
	
	#检测页面编码
	#coding = chardet.detect(str1)

	#对大文件进行编码识别
	#创建一个检测对象
	detector = UniversalDetector()
	#在内存中读写str
	buf = StringIO.StringIO(html)
	for line in buf.readlines():
		#分块进行测试，直到达到阈值
		#print line
		detector.feed(line)
		if detector.done: 
			break
	#关闭检测对象
	detector.close()
	buf.close()
	#检测结果
	coding = detector.result

	#匹配中文部分
	#coding['encoding']！=0，即存在就执行
	if coding['encoding']:
		#content = unicode(str1,coding['encoding'])
		content = html.decode(coding['encoding'],'ignore')

		#正则表达式匹配至少一个中文
		re_words = re.compile(u"[\u4e00-\u9fa5]+")
	  	#以列表形式返回匹配的字符串
		res = re.findall(re_words, content)
		#返回的res已经是字符串格式了，为什么还要转成字符串格式？？？
		#res输出是uncoide，str_convert输出是中文    
		str_convert = ' '.join(res)
		#输出中文页面
		#print str_convert
	return str_convert

#函数：提取关键字
def get_tips(content):
	#结巴分词提取关键字
	tags = jieba.analyse.extract_tags(content,topK) 
	tag = ",".join(tags)
	print tag
	return tag


#主函数
if __name__ == "__main__":
	#连接数据库
	conn = getMysqlConn()
	cur = conn.cursor()
	#print "connect mysql success"

	#查询种子站点
	select_sql = getSelectMysql()
	cur.execute(select_sql)
	urls = cur.fetchall()

	#charu_url = insert_url()
	#charu_tip = insert_tip()

	for domain in urls[:3]:
		try:
			#url = 'http://www.freebuf.com'
			#获取全部url
			domain = domain[0]
			print "===================="
			print domain
	
			get_url = spider_url(domain)
			#print get_url
		
			#筛选url
			select_url = filter_url(get_url,domain)
			#print select_url	

			content_all = []

			for url in select_url:
				#print url

				#把过滤后的url和种子站点插入数据库
				sql="insert into freebuf_secpulse.urls(siteDomain,url) values('%s','%s')" %(domain,url)
				try:
					print sql
					cur.execute(sql)
					conn.commit()
				except:
					traceback.print_exc()
					conn.rollback()


				#获取页面中文内容
				content = get_content(url)
				if content != 0:
					content_all.append(content)
					
			content_url = " ".join(content_all)

			tips = get_tips(content_url)

			time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

			#把标签和url插入到数据库
			sql="insert into freebuf_secpulse.tips(siteDomain,tips,createTime) values('%s','%s','%s')" %(domain,tips,time)
			try:
				print sql
				cur.execute(sql)
				conn.commit()
			except:
				traceback.print_exc()
				conn.rollback()
 
		except:
			traceback.print_exc()
	
	
	#提交数据，关闭数据库
	cur.close()
	conn.close()
	
