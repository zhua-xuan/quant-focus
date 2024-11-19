#encoding:gbk

import pandas as pd
import numpy as np
from datetime import datetime
import datetime
import winsound
import pickle
import os
import time
import statistics

class a():
	pass
A = a()
buy_list = []

def init(C):
	C.stock=C.get_stock_list_in_sector('沪深A股') #获取沪深所有A股
	C.stock = list({stock for stock in C.stock if 'ST' not in C.get_stock_name(stock)})
	C.stock = list({stock for stock in C.stock if '退' not in C.get_stock_name(stock)})
	A.stock = C.stock
	#C.set_universe(A.stock)
	A.line5=5;A.line10=10;A.line20=20;A.line60=60;A.line120=120;A.line250=250
	#A.buy = True; A.sell = False #True表示可以执行这个操作，False不可以
	A.acct = '0260009266' #账号为模型交易界面选择账号
	A.acct_type = 'STOCK' #账号类型为模型交易界面选择账号
	A.amount = 50000 #单笔买入金额 触发买入信号后买入指定金额
	A.buy_code = 23 if A.acct_type == 'STOCK' else 33 #买卖代码 区分股票 与 两融账号
	A.sell_code = 24 if A.acct_type == 'STOCK' else 34

def pma(closePrice,ma5,ma10,ma20,ma60,ma120,ma250):    #价格大于六条均线            
	if closePrice > max(ma5,ma10,ma20,ma60,ma120,ma250):
		#if ma250 > max(ma5,ma10,ma20,ma60,ma120):
			#if ma250 / min([x for x in [ma5,ma10,ma20,ma60,ma120] if x != 0]) - 1 < 0.05:
		return True
	else:
		return False

def ma_plus(ma1,ma2,yma1,yma2,type):   #10和20组合斜率条件
	if type == 1:
		if ma1 * ma2 * yma1 * yma2 == 0:
			return False
		elif ma1/yma1 + ma2/yma2 > 1.995:
			return True
		else:
			return False
	elif type == 2:
		if ma1 * yma1 == 0:   #120线没有
			return True
		elif ma2 * yma2 == 0:  #250没有
			if ma1/yma1 >= 0.98:
				return True
			else:
				return False
		else:
			if ma1/yma1 + ma2/yma2 >= 2:
				return True
			else:
				return False

def ma_slope(ma,yma,type):   #均线斜率
	if type == 60: 
		if ma * yma == 0 or ma/yma >= 0.99:
			return True
	else:
		return False

def ma5_slope(ma,yma,yyma):   #5日均线斜率
	if ma * yma * yyma == 0:
		return False
	if ma/yma > 1.0179:
		return True
	else:
		return False


def WR(C,stock,yesterday):
	score =[]
	for countday in [10,20,120]:
		WR = [];low = []
		data_close = C.get_market_data_ex(['close','high','low'], [stock],period='1d',end_time = yesterday,count=countday,dividend_type='front', fill_data=False, subscribe=False)
		data_close = np.array(data_close[stock])
		for i in range(len(data_close)):
			low.append(data_close[i][2])
		LN = min(low)
		for i in range(len(data_close)):
			TYP = (data_close[i][0]+data_close[i][1]+data_close[i][2])/3
			WR.append((TYP*2-LN))
		result_temp = statistics.pstdev(WR)/statistics.mean(WR)
		score.append(result_temp)
	result = 0.3*score[0]+0.4*score[1]+0.3*score[2]
	return result,score[2]

def ATR_Result(C,stock,yesterday):
	score =[];ATR=[]
	for countday in [10,20,120]:
		TR = []
		data_price = C.get_market_data_ex(['high','low'], [stock],period='1d',end_time = yesterday,count=countday,dividend_type='front', fill_data=False, subscribe=False)
		data_close = C.get_market_data_ex(['close'], [stock],period='1d',end_time = yesterday,count=countday+1,dividend_type='front', fill_data=False, subscribe=False)
		data_price = np.array(data_price[stock])
		data_close = np.array(data_close[stock])
		data_close = data_close[:-1]
		for i in range(len(data_close)):
			mincl = min(data_close[i][0],data_price[i][1])
			minch = min(data_close[i][0],data_price[i][0])
			max_result = max(abs(data_price[i][0]-data_price[i][1])/data_price[i][1],abs(data_close[i][0]-data_price[i][0])/minch,abs(data_close[i][0]-data_price[i][1])/mincl)   #比例
			TR.append(max_result)
		ATR.append(sum(TR)/len(TR))
	#可以写10日的大于阈值设为0，小于为1，20、120同，阈值不同
	result = 0.3*ATR[0]+0.4*ATR[1]+0.3*ATR[2]
	return result

def BOLL(C,stock,MA20,list):
	MD = statistics.pstdev(list)
	UP = MA20 + 2 * MD
	return UP

def handlebar(C):
	global buy_list
	if not C.is_last_bar(): #跳过历史k线
		return
	now = datetime.datetime.now()
	now_time = now.strftime('%H%M%S') 

	account = get_trade_detail_data(A.acct, A.acct_type, 'account')
	if len(account)==0:
		print(f'账号{A.acct} 未登录 请检查')
		return

	#计算今天日期和昨天日期
	d = C.barpos
	timetag = C.get_bar_timetag(d)
	today = timetag_to_datetime(timetag, '%Y%m%d')
	yesterday = datetime.date.today() - datetime.timedelta(days=1)
	yesterday = yesterday.strftime("%Y%m%d")
	#yesterday = '20231103'
	for i in range(len(A.stock)):
		if C.is_suspended_stock(A.stock[i],1):
			continue

		#计算六条均线
		close_list = [];high_list = [];yy_count = [];volume_flag = False;volume_list = [];closepn_list = [];volumepn_list = []
		data_close = C.get_market_data_ex(['close'], [A.stock[i]],period='1d',end_time = yesterday,count=251,dividend_type='front', fill_data=False, subscribe=False)
		data_close = np.array(data_close[A.stock[i]])
		for value in data_close:
			close_list.append(value[0])
		
		data_high = C.get_market_data_ex(['high'],[A.stock[i]],period='1d',end_time = yesterday,count=1,dividend_type='front', fill_data=False, subscribe=False)
		data_high = np.array(data_high[A.stock[i]])
		for value in data_high:
			high_list.append(value[0])
		
		#阳线阴线数
		yy_price = C.get_market_data_ex(['open','close'], [A.stock[i]],period='1d',end_time = yesterday,count=17,dividend_type='front', fill_data=False, subscribe=False)
		yy_price = np.array(yy_price[A.stock[i]])
		data_tick = C.get_full_tick([A.stock[i]])
		tick_price = data_tick[A.stock[i]]['lastPrice']
		close_list.append(tick_price)
		for value in yy_price:
			if (value[1] - value[0]) >= 0:
				yy_count.append(1)
			else:
				yy_count.append(-1)   #sum yy_count要大于1

		#成交量阴阳
		for h in range(6):
			if len(close_list) > 6:
				if close_list[-6+h] >= close_list[-7+h]:
					closepn_list.append(1)
				else:
					closepn_list.append(-1)
			else:
				closepn_list = [0,0,0,0,0,0]
		#成交量前四天和大于0，昨天大于0，前天大于昨天-0.6
		data_tick = C.get_full_tick([A.stock[i]])
		pvolume = data_tick[A.stock[i]]['pvolume']  #今天的成交量
		data_volume_list = []
		data_volume = C.get_market_data_ex(['volume'], [A.stock[i]],period='1d',end_time = yesterday,count=120,dividend_type='front', fill_data=False, subscribe=False)
		data_volume = np.array(data_volume[A.stock[i]])
		for value in data_volume:
			data_volume_list.append(value[0])
		data_volume_list.append(pvolume/100)
		if len(data_volume) > 6:
			for h in range(6):   #精看六天的成交量
				volumepn_list.append(data_volume_list[-6+h]*closepn_list[-6+h])
		else:
			volumepn_list = [0,0,0,0,0,0]
		mean_volumepn_list = sum(volumepn_list)/len(volumepn_list)
		#print(A.stock[i],mean_volumepn_list)
		#print(A.stock[i],volumepn_list)
		if sum(volumepn_list) > 0 and volumepn_list[-1] > 0 and volumepn_list[-2] > - 2 * abs(volumepn_list[-1]) and volumepn_list[-3] > - 2 * abs(volumepn_list[-1]):
			volume_flag = True
			
		#当天/五天/一个月有过巨量换手率(没)
		turn_flag = False
		for value in data_volume:
			volume_list.append(value[0])
		volume_list.append(pvolume/100)
		stock_volume = C.get_last_volume(A.stock[i])
		#fvolume = C.get_instrumentdetail(A.stock[i])
		#print(A.stock[i],fvolume)
		turn = []
		if stock_volume != 0:
			mean_volume_list = sum(volume_list)/len(volume_list)
			turn_mean = mean_volume_list/stock_volume
			for value in volume_list:
				turn.append(value/stock_volume)
		if len(turn) > 19:
			for h in range(20):  #一个月内有大于半年的换手
				if turn[-20+h] > turn_mean:
					turn_flag = True
					break

		high_list.append(data_tick[A.stock[i]]['high'])
		tick_price = data_tick[A.stock[i]]['lastPrice']
		close_list.append(tick_price)
		len_close_list = len(close_list)
		
		#涨停过(没)
		#spread_flag = False
		#long = int(0.5 * len_close_list)
		#for m in range(long):
			#spread_rate = close_list[-long+1+m]/close_list[-long+m] - 1
			#if spread_rate > 0.095:
				#spread_flag = True
				#break

		#计算均线
		ppre_line5 = np.mean(close_list[-A.line5-2: -2]) if len_close_list>6 else 0
		ppre_line10 = np.mean(close_list[-A.line10-2: -2]) if len_close_list>11 else 0
		ppre_line20 = np.mean(close_list[-A.line20-2: -2]) if len_close_list>21 else 0
		ppre_line120 = np.mean(close_list[-A.line120-2: -2]) if len_close_list>121 else 0
		ppre_line250 = np.mean(close_list[-A.line250-2: -2]) if len_close_list>251 else 0
		pre_line5 = np.mean(close_list[-A.line5-1: -1]) if len_close_list>5 else 0
		pre_line10 = np.mean(close_list[-A.line10-1: -1]) if len_close_list>10 else 0
		pre_line20 = np.mean(close_list[-A.line20-1: -1]) if len_close_list>20 else 0
		pre_line60 = np.mean(close_list[-A.line60-1: -1]) if len_close_list>60 else 0
		pre_line120= np.mean(close_list[-A.line120-1: -1]) if len_close_list>120 else 0
		pre_line250 = np.mean(close_list[-A.line250-1: -1]) if len_close_list>250 else 0
		current_line5 = np.mean(close_list[-A.line5: ]) if len_close_list>4 else 0
		current_line10 = np.mean(close_list[-A.line10: ]) if len_close_list>9 else 0
		current_line20 = np.mean(close_list[-A.line20: ]) if len_close_list>19 else 0
		current_line60 = np.mean(close_list[-A.line60: ]) if len_close_list>59 else 0
		current_line120 = np.mean(close_list[-A.line120: ]) if len_close_list>119 else 0
		current_line250 = np.mean(close_list[-A.line250: ]) if len_close_list>249 else 0

		#设置选股条件的响应Flag
		pFlag = False; ma5slopeFlag = 0; slopeFlag = False
		if pma(tick_price,current_line5,current_line10,current_line20,current_line60,current_line120,current_line250):
			pFlag = True    #价是否大于六根均线
		if (pFlag and ma_plus(pre_line10,pre_line20,ppre_line10,ppre_line20,1) and ma_plus(pre_line120,pre_line250,ppre_line120,ppre_line250,2) and ma_slope(current_line60,pre_line60,60)):
			slopeFlag = True
		if slopeFlag: #数据问题可能取空
			#若ma5slopeFlag为1，则一定也满足换手率条件
			ma5slopeFlag = ma5_slope(current_line5,pre_line5,ppre_line5) * 1

		#买入条件：价大于六条均线、ma60>=0.999、昨天120+250斜率大于等于1.998、昨天10+20斜率大于1.95、换手率大于4%、ma5>1.016、range小于等于25%、没有涨停封板、涨跌幅小于16%
		if A.stock[i] not in buy_list:
			if bool(ma5slopeFlag):
				#if data_tick[A.stock[i]]['askPrice'][1] != 0:
				if volume_flag and sum(yy_count) >= -2:
					WR_result,WR_120 = WR(C,A.stock[i],yesterday)
					ATR = ATR_Result(C,A.stock[i],yesterday)
					Boll = BOLL(C,A.stock[i],current_line20,close_list[-20:])
					if WR_result < 0.12 and (Boll-tick_price)/tick_price < 0.02:
						#if tick_price <= 9:
						print('买入：',C.get_stock_name(A.stock[i]),' ',A.stock[i])
						buy_list.append(A.stock[i])
	with open('D:/account_data/my_holdings.pickle', 'wb') as h:
		pickle.dump(buy_list, h)