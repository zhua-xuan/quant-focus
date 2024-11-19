#encoding:gbk

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
import time
import statistics
from scipy import signal


class a():
	pass
A = a()

count = 0

def init(C):
	C.stock=C.get_stock_list_in_sector('沪深A股') #获取沪深所有A股
	C.stock = list({stock for stock in C.stock if 'ST' not in C.get_stock_name(stock)})
	C.stock = list({stock for stock in C.stock if '退' not in C.get_stock_name(stock)})
	A.stock = C.stock
	A.acct = '0260009266' #账号为模型交易界面选择账号
	A.acct_type = 'STOCK' #账号类型为模型交易界面选择账号
	huang(C)

def handlebar(C):
	if not C.is_last_bar():
		return

def huang(C):
	Al = len(A.stock)
	for i in range(Al):
		if C.is_suspended_stock(A.stock[i],1):
			continue
		price_list = [];close_list = []
		data_price = C.get_market_data_ex(['close'], [A.stock[i]],period='5m',end_time = '20231206',count=20,dividend_type='front', fill_data=False, subscribe=False)
		#print(A.stock[i],data_price)
		data_price = np.array(data_price[A.stock[i]])
		for value in data_price:
			price_list.append(value[0])
		#print(A.stock[i],price_list)
		data_close = C.get_market_data_ex(['close'], [A.stock[i]],period='1d',end_time = '20231205',count=1,dividend_type='front', fill_data=False, subscribe=False)
		data_close = np.array(data_close[A.stock[i]])
		for value in data_close:
			close_list.append(value[0])
		#print(A.stock[i],close_list)
		if len(close_list) > 0 and close_list[0]!= 0:
			l = len(price_list)
			if l > 0:
				origin = price_list[0]/close_list[0] - 1
				if origin <= 0.1:
					for j in range(l):
						now = price_list[j]/close_list[0] - 1
						if now - origin >= 0.05:
							end = price_list[-1]/close_list[0] - 1
							if now - end >= 0.02:
									print('下午冲高回落：',C.get_stock_name(A.stock[i]),A.stock[i])
									break

						else:
							continue
						break
	print('end')