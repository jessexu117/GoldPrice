#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
本文件使用data文件夹下的neg.txt和pos.txt情感语料库对snownlp包的情感分析进行训练，提高情感分析准确率
由于未找到合适的语料库资源>_<,人为分类语料库信息效率极低(我尝试过...), 故我直接使用snownlp默认的购买商品评价语料库...
此处后续后提升
"""
from snownlp import sentiment
import os


path = os.path.abspath(os.path.dirname(__file__))
price_data_path = os.path.join(path+'/data/', price_file_name)

sentiment.train('neg.txt', 'pos.txt')
sentiment.save(path[:-5]+'/snownlp/sentiment/gold_sentiment.marshal')

# 训练完后在/snownlp/sentiment文件夹下__init__.py修改指定的marshal文件才可使用
