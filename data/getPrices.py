#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
本文件功能：获取黄金历史价格
操作上直接对新浪财经数据下载链接进行日期修改，然后请求数据下载为csv格式文件
文件内容包括：日期 合约 开盘价 最高价 最低价 收盘价 涨跌额 涨跌幅 加权平均价 成交量(公斤) 交金额(元)
文件储存在data文件夹下面：文件名为'AUTD_hist_data_'+start_date+'_'+end_date+'.csv'
"""
import requests
import csv
from datetime import *

start_date = date.today() - timedelta(days=365*2)
end_date = date.today()
url = 'http://vip.stock.finance.sina.com.cn/q/view/download_gold_history.php?breed=AUTD&start='+str(start_date)+'&end='+str(end_date)

res = requests.get(url)  # AUTD price
res.raise_for_status()
res.encoding = 'gbk'

file_name ='AUTD_hist_data_'+str(start_date)+'_'+str(end_date)+'.csv'
with open(file_name, 'wb') as f:
    head = 'contract\topen\thigh\tlow\tclose\tchange\tchgRate\taverage\tvolume\tturnover\n'
    f.write(head)
    print res.text
    for line in res.text.split('\n')[1:]:
        f.write(line+'\n')
