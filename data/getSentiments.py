#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
本文件功能：对getNews.py爬取得新闻数据进行情感分析，并将相应日期新闻对应的新闻情感得分取均值存入数据库
此处可拓展，可扩大舆情数据种类，如论坛评论，机构观点，美元指数新闻数据，通胀数据等。
对不同数据种类进行情感分析可得多种情感数据。
技术上用SQlite3包连接数据库，用SnowNLP包进行情感分析，时间大概需要20分钟。
此外可对SnowNLP包的情感分析语料库进行更新重训练，可得更好的评分结果。
sentiment数据值说明：都介于[0,1]之间，大于0.5说明pos概率较高，小于0.5说明neg概率较高
"""
from __future__ import unicode_literals
from snownlp import SnowNLP
import sqlite3
import numpy as np

db_file_path = 'goldNews.db'  # SQLite 数据库名称，路径为当前目录

conn = sqlite3.connect(db_file_path)
conn.row_factory = sqlite3.Row

cur = conn.cursor()
cur.execute("SELECT date FROM News")

rows = cur.fetchall()
date_set = set()
for row in rows:
    print row
    date_set.add(row[0])
date_dic = {}

for date in list(date_set):
    date_dic[date] = []

cur.execute("SELECT date, summary FROM News")
rows = cur.fetchall()
for row in rows:
    sen = SnowNLP(row[1])
    date_dic[row[0]].append(sen.sentiments)

for key, value in date_dic.iteritems():
    date_dic[key] = (np.array(value)).mean()

# cur.execute('''CREATE TABLE sentiments(date TEXT PRIMARY KEY NOT NULL, sentiment REAL);''')

sql = "INSERT INTO sentiments(date, sentiment) VALUES(?,?)"
cur.executemany(sql, date_dic.items())

conn.commit()
conn.close()

print "Operation done successfully";
