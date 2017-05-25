#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
本文件采用gcForests深度森林算法基于金价历史交易数据和新闻情感数据进行训练，并验证模型效果。
我使用了两年的交易数据和新闻数据建模(2015-5-10 ~ 2017-5-10)
操作上，首先对黄金价格和情感数据进行数据整合(整理成一个DataFrame)，然后选取一些特征和新闻情感数据进行训练。
然后对训练好的模型进行评估，得到预测准确率。
由于特征工程和特征选择是机器学习实践领域的核心，且不断调参的时间成本和训练的计算资源成本较高，
此处我仅仅采用一些基本的交易数据和情感数据做特征。
后期提升包括：
对数据进行正则化处理;
采用TA-Lib(技术分析库)对交易数据进行技术指标的合成(ATR,MAcd,EMA,RSI,VAR等指标)然后作为特征训练;
扩大情感数据的种类，也可对情感数据进行合成。
"""
from gcForest import *
from sklearn.model_selection import train_test_split # 从样本中随机的按比例选取train data和test data
from sklearn.metrics import accuracy_score # 导入分类准确率指标
from sklearn import preprocessing

from datetime import *
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sqlite3
import os

start_date = (datetime.today() - timedelta(days=365*2)).strftime("%Y-%m-%d")
end_date = datetime.today().strftime("%Y-%m-%d")

price_file_name = 'AUTD_hist_data_'+start_date+'_'+end_date+'.csv'

path = os.path.abspath(os.path.dirname(__file__))
price_data_path = os.path.join(path+'/data/', price_file_name)

# colume_names = ['contract','open','high','low','close','chg','chgRate','average','volume','turnover']

df_price = pd.DataFrame.from_csv(price_data_path, sep='\t')

db_file_name = 'goldNews.db'  # SQLite 数据库名称，路径为当前目录
db_file_path = os.path.join(path+'/data/', db_file_name)

conn = sqlite3.connect(db_file_path)
conn.row_factory = sqlite3.Row

cur = conn.cursor()
cur.execute("SELECT * FROM sentiments")

rows = cur.fetchall()
time_index = []
sentiment_list = []
for row in rows:
    dat = datetime.strptime(row[0], "%Y-%m-%d")
    time_index.append(dat)
    sentiment_list.append(row[1])
conn.close()

df_sentiment = pd.DataFrame(sentiment_list, index=time_index,columns=['sentiment'])

df = pd.merge(df_price,df_sentiment,left_index=True,right_index=True,how='outer').dropna()

# print np.array(df)
open = df['open'].values
close = df['close'].values
# volume = df['volume'].values
average = df['average'].values
sentiment = df['sentiment'].values

X = np.array([open, close, average, sentiment]).T
y= []
change = df['change'].values
for i in range(len(change)):
    if change[i] > 0:
        y.append(1)
    else:
        y.append(0)

y = np.array(y)

# 把数据集分解成随机的训练和测试子集， 参数test_size表示测试集所占比例
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.33)

# shape_1X样本维度，window为多粒度扫描（Multi-Grained Scanning）算法中滑动窗口大小，\
# 用于扫描原始数据，tolerance为级联生长的精度差,整个级联的性能将在验证集上进行估计，\
# 如果没有显着的性能增益，训练过程将终止
gcf = gcForest(shape_1X=4, n_mgsRFtree=100, window=3, stride=2,
                 cascade_test_size=0.2, n_cascadeRF=4, n_cascadeRFtree=101, cascade_layer=np.inf,
                 min_samples_mgs=0.1, min_samples_cascade=0.1, tolerance=0.0, n_jobs=1)
gcf.fit(X_tr, y_tr)
# gcf = gcForest(shape_1X=5, window=2, tolerance=0.0)
# gcf = gcForest(shape_1X=[5,5], window=2, tolerance=0.0)
# gcf = gcForest(shape_1X=[1,5], window=[1,6],)
# gcf.fit(X_tr, y_tr)

pred_X = gcf.predict(X_te)

# 保存每一天预测的结果，如果某天预测对了，保存1，如果某天预测错了，保存-1
result_list = []


# 检查预测是否成功
def checkPredict(i):
    if pred_X[i] == y_te[i]:
        result_list.append(1)
    else:
        result_list.append(0)

# 画出最近第k+1个长度为j的时间段准确率
k = 0
j = len(y_te)
# j=100
for i in range(len(y_te) - j * (k + 1), len(y_te) - j * k):
    checkPredict(i)
    # print(y_pred[i])
    # return result_list
# print(len(y_te))
# print(len(result_list))

# 将准确率曲线画出来
x = range(0, len(result_list))
y = []
# z=[]
for i in range(0, len(result_list)):
    # y.append((1 + float(sum(result_list[:i])) / (i+1)) / 2)
    y.append(float(sum(result_list[:i])) / (i + 1))
print 'Total '+str(j)+' times forecasting with a accuracy: ', y[-1]
# print(x, y)
line, = plt.plot(x, y)
plt.show()

# 评估准确率
accuracy = accuracy_score(y_true=y_te, y_pred=pred_X)
print('gcForest accuracy : {}'.format(accuracy))
