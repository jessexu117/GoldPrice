#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
本文件功能：从黄金头条网站爬取市场黄金要闻，并将数据存入SQLite数据库
设计上可支持多线程爬取，但由于任务量不大，30分钟即可爬取两年所有新闻数据，故为采用多线程
爬取的新闻内容包括：新闻时间+新闻标题+新闻摘要，新闻主体内容由于情感分析效果较差故跳过
然后存入SQLite数据库
"""
from datetime import datetime
from bs4 import BeautifulSoup
from Queue import Queue
import requests
import re
import inspect
import threading
import time

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Integer, Date, String, TEXT
from sqlalchemy.orm import sessionmaker

# 创建模型的基类
BaseModel = declarative_base()


# 定义自己的模型
class News(BaseModel):
    __tablename__ = 'news'
    id = Column(Integer, primary_key=True)  # 默认 autoincrement=True
    date = Column(Date)
    title = Column(String(50))
    summary = Column(String(500))
    # content = Column(String(2000))

    def __init__(self, date, title, summary):
        self.date = date         # 新闻时间
        self.title = title       # 新闻标题
        self.summary = summary   # 新闻摘要
        # self.content = content   # 新闻内容

    def __str__(self):
        return '%s\t%s\t%s' % (str(self.date), self.title.encode("UTF-8"), self.summary.encode("UTF-8"))

    def __repr__(self):
        return '<News(%d, %s, %s, %s)>' % (self.id, str(self.date), self.title, self.summary)


class Database(object):
    def __init__(self, path):
        # 创建一个内存 sqlite 数据库
        self.engine = create_engine('sqlite:///' + path, encoding="UTF-8", echo=False)
        BaseModel.metadata.create_all(self.engine)   # 创建所有模型对应的数据库表
        DB_Session = sessionmaker(bind=self.engine)
        self.session = DB_Session()

    def insertNews(self, news):
        try:
            self.session.add(news)
            self.session.commit()
        except Exception, e:
            print type(e), e
            self.session.rollback()


class ThreadPool(object):   # 线程池
    def __init__(self, thread_num, worker, queue): # queue 必须是线程安全的。
        assert isinstance(thread_num, int)
        assert inspect.isfunction(worker)
        assert isinstance(queue, Queue)
        self.queue = queue
        self.threads = []
        self.stop_event = threading.Event()
        for i in range(0, thread_num):
            thread = threading.Thread(name='Thread-' + str(i), target=worker, args=(self.queue, self.stop_event, ))
            self.threads.append(thread)
        for thread in self.threads:
            thread.start()

    def join(self, wait_until_all_task_done=True):
        # 等到所有任务完成
        if wait_until_all_task_done:
            self.queue.join()
        # 设置线程结束标志
        self.stop_event.set()
        for thread in self.threads:
            thread.join()


def getList(url):   # 获取新闻链接地址
    url_head = url[:28]    # https://www.goldtoutiao.com/

    news_list = requests.get(url)
    res = r'<a class="title" href="/post/.*?">' # 正则表达式获取链接地址
    urls = re.findall(res, news_list.text)
    for i in range(len(urls)):
        urls[i] = url_head + urls[i][24:-2]
    return urls

def getNews(url):  # 获取新闻内容
    res = requests.get(url)
    res.encoding = 'UTF-8'
    soup = BeautifulSoup(res.text, "lxml")  # 获取新闻内容，注意编码

    date = soup.find('span', 'item time').get_text().encode('UTF-8')
    date = date[:4]+'-'+date[7:9]+'-'+date[12:14]   # 日期格式提取

    title = soup.title.string[:-5].encode('UTF-8').decode('UTF-8')       # 新闻标题提取
    try:
        summary = soup.find('div', class_='summary').get_text()[24:]
    except Exception, e:
        # print type(e), e
        tags = soup.find_all(align="justify")
        if len(tags) <> 0:
            summary = tags[0].get_text()
        else:
            tag = soup.find('div', class_='content').find_all(['p', 'div'])[1]
            # if 'href' in str[tag]:
            #     tag = soup.find('div', class_='content').find_all(['p', 'div'])[1]
            #     summary = tag.get_text()
            # else:
            summary = tag.get_text()
        if len(summary) < len(title):
            summary = title
    '''
    news_tags = soup.find_all(align="justify")      # 新闻内容提取
    content = str()
    for tag in news_tags:       # 简短list新闻类型爬取
        content += tag.get_text()

    if len(content) == 0:
        news_tags = soup.find('div', class_='content')      # Article新闻类型爬取
        for tag in news_tags.find_all(['p', 'div']):
            if 'href' in str(tag):
                continue
            content += tag.get_text()
    '''
    news = News(datetime.strptime(date, "%Y-%m-%d"), title, summary)

    return news


if __name__ == "__main__":

    start = time.clock()
    db_file_path = 'goldNews.db'   # SQLite 数据库名称，路径为当前目录
    news_db = Database(db_file_path)

    # 黄金头条>市场新闻>黄金要闻 2014-05-30 -> present
    init_url = 'https://www.goldtoutiao.com/news/list?status=published&cid=3&order=-created_at&limit=25&page='
    start_page = 173
    end_page = 300
    print u'开始解析...'
    sum = 0   # 新闻计数
    for i in range(start_page, end_page):
        url = init_url + str(i)
        urls = getList(url=url)
        sum += len(urls)
        j = 1
        for u in urls:
            print u"正在读取第%s页第%s/%s条:%s" % (i, j, len(urls), u.encode('UTF-8'))
            news = getNews(url=u)
            news_db.insertNews(news)
            j += 1

    end = time.clock()
    print "共爬取%s条新闻，耗时 %f s" %(sum, end - start)
