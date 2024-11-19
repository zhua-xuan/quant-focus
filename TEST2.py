#encoding:gbk

import pandas as pd
import numpy as np
from datetime import datetime
import datetime
import winsound
import pickle
import os
import time

class a():
	pass
A = a()

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
	A.amount = 15300 #单笔买入金额1.6%
	A.buy_code = 23 if A.acct_type == 'STOCK' else 33 #买卖代码 区分股票 与 两融账号
	A.sell_code = 24 if A.acct_type == 'STOCK' else 34

#选股判断函数
def pma(closePrice,ma5,ma10,ma20,ma60,ma120,ma250):    #价格大于六条均线            
		if closePrice > max((ma5,ma10,ma20,ma60,ma120,ma250)):
			return True
		else:
			return False

def ma_slope(ma,yma,type):   #均线斜率
		if type == 20:
			if ma * yma == 0:
				return False
			elif ma/yma > 0.995:
				return True
		elif type == 60: 
			if ma * yma == 0 or ma/yma >= 0.999:
				return True
		elif type == 120:
			if ma * yma == 0 or ma/yma >= 1:
				return True
		elif type == 250:
			if ma * yma == 0 or ma/yma >= 1:
				return True
		else:
			return False

def ma5_slope(ma,yma,yyma):   #5日均线斜率
		if ma * yma * yyma == 0:
			return False
		if ma/yma > 1.0175 and yma/yyma <= 1.0175:
			return True
		else:
			return False

def handlebar(C):
	global holdings; global stock_sell
	if not C.is_last_bar(): #跳过历史k线
		return
	now = datetime.datetime.now()
	now_time = now.strftime('%H%M%S') 
	if now_time < '093000' or now_time > "150000" or (now_time > "113000" and now_time < "130000"):  #跳过非交易时间
		return

	account = get_trade_detail_data(A.acct, A.acct_type, 'account')
	if len(account)==0:
		print(f'账号{A.acct} 未登录 请检查')
		return
	available_cash = int(account[0].m_dAvailable)
	orders = get_trade_detail_data(A.acct,A.acct_type,'order')
	positions = get_trade_detail_data(A.acct,A.acct_type,'position')
	holdings = {i.m_strInstrumentID + '.' + i.m_strExchangeID : [i.m_nVolume,i.m_nCanUseVolume] for i in positions}
	orders_buy = {i.m_strInstrumentID + '.' + i.m_strExchangeID : [i.m_nVolumeTotal,i.m_strOrderSysID,i.m_strInsertTime] for i in orders if i.m_strOptName == '限价买入'}  #买入的
	orders_sell = {i.m_strInstrumentID + '.' + i.m_strExchangeID : [i.m_nVolumeTotal,i.m_strOrderSysID,i.m_strInsertTime,i.m_dCancelAmount] for i in orders if i.m_strOptName == '限价卖出'}  #卖出的

	#计算今天日期和昨天日期
	d = C.barpos
	timetag = C.get_bar_timetag(d)
	today = timetag_to_datetime(timetag, '%Y%m%d')
	yesterday = datetime.date.today() - datetime.timedelta(days=1)
	yesterday = yesterday.strftime("%Y%m%d")

	for i in range(len(A.stock)):
		if C.is_suspended_stock(A.stock[i],1):
			continue

		#计算六条均线
		close_list = [];high_list = []
		#data_price=C.get_local_data(stock_code=A.stock[i],end_time = yesterday,period='1d',divid_type='front',count=251)
		data_close = C.get_market_data_ex(['close'], [A.stock[i]],period='1d',end_time = yesterday,count=251,dividend_type='front', fill_data=False, subscribe=False)
		data_close = np.array(data_close[A.stock[i]])
		for value in data_close:
			close_list.append(value[0])
		data_high = C.get_market_data_ex(['high'],[A.stock[i]],period='1d',end_time = yesterday,count=1,dividend_type='front', fill_data=False, subscribe=False)
		data_high = np.array(data_high[A.stock[i]])
		for value in data_high:
			high_list.append(value[0])

		data_tick = C.get_full_tick([A.stock[i]])
		high_list.append(data_tick[A.stock[i]]['high'])
		tick_price = data_tick[A.stock[i]]['lastPrice']
		close_list.append(tick_price)

		ppre_line5 = np.mean(close_list[-A.line5-2: -2]) if len(close_list)>6 else 0
		pre_line5 = np.mean(close_list[-A.line5-1: -1]) if len(close_list)>5 else 0
		pre_line20 = np.mean(close_list[-A.line20-1: -1]) if len(close_list)>20 else 0
		pre_line60 = np.mean(close_list[-A.line60-1: -1]) if len(close_list)>60 else 0
		pre_line120= np.mean(close_list[-A.line120-1: -1]) if len(close_list)>120 else 0
		pre_line250 = np.mean(close_list[-A.line250-1: -1]) if len(close_list)>250 else 0
		current_line5 = np.mean(close_list[-A.line5: ]) if len(close_list)>4 else 0
		current_line10 = np.mean(close_list[-A.line10: ]) if len(close_list)>9 else 0
		current_line20 = np.mean(close_list[-A.line20: ]) if len(close_list)>19 else 0
		current_line60 = np.mean(close_list[-A.line60: ]) if len(close_list)>59 else 0
		current_line120 = np.mean(close_list[-A.line120: ]) if len(close_list)>119 else 0
		current_line250 = np.mean(close_list[-A.line250: ]) if len(close_list)>249 else 0

		#计算换手率
		volume = C.get_last_volume(A.stock[i])
		turnover = C.get_turnover_rate([A.stock[i]],today,today)
		#data_v = C.get_market_data_ex(['volume'], [A.stock[i]],period='1d',start_time = '20230804',end_time='20230804',dividend_type='front', fill_data=False, subscribe=False)
		#yturnover = data_v[A.stock[i]].iloc[-1,0]*100/volume
		yturnover = C.get_turnover_rate([A.stock[i]],yesterday,yesterday)
		if not turnover.empty:
			turnover = turnover.iloc[-1,0]
		else:
			turnover = 0
			data_tick = C.get_full_tick([A.stock[i]])
			#volume = C.get_last_volume(A.stock[i])
			pvolume = data_tick[A.stock[i]]['pvolume']
			if volume != 0:
				turnover = pvolume/volume

		if not yturnover.empty:
			yturnover = yturnover.iloc[-1,0]
		else:
			yturnover = 0
			data_v = C.get_market_data_ex(['volume'], [A.stock[i]],period='1d',start_time = yesterday,end_time=yesterday,dividend_type='front', fill_data=False, subscribe=False)
			if not data_v[A.stock[i]].empty and volume != 0:
				yturnover = data_v[A.stock[i]].iloc[-1,0]*100/volume

		if tick_price != 0:
			vol = int(A.amount / tick_price / 100) * 100 #买入数量 向下取整到100的整数倍
		#设置选股条件的响应Flag
		pFlag = False; ma5slopeFlag = False; slopeFlag = False
		if pma(tick_price,current_line5,current_line10,current_line20,current_line60,current_line120,current_line250):
			pFlag = True    #价是否大于六根均线
		if (pFlag and ma_slope(current_line20,pre_line20,20) and ma_slope(current_line60,pre_line60,60) and ma_slope(current_line120,pre_line120,120) and ma_slope(current_line250,pre_line250,250)):
			slopeFlag = True
		if slopeFlag and (turnover > 0.042 or yturnover > 0.042 ): #数据问题可能取空
			#若ma5slopeFlag为1，则一定也满足换手率条件
			ma5slopeFlag = ma5_slope(current_line5,pre_line5,ppre_line5) * 1

		#买入条件：价大于六条均线、ma20>0.995&ma60>0.999&ma120>=1&ma250>=1、换手率大于4%和ma5>1.0175
		if A.amount < available_cash and vol >= 100 and A.stock[i] not in holdings.keys() and A.stock[i] not in orders_buy:
			if pFlag and slopeFlag and bool(ma5slopeFlag):
				if available_cash < 30000:
					time.sleep(12)
				passorder(A.buy_code, 1101, A.acct, A.stock[i], 0, -1, vol, 1 , C)


		#卖出条件：价格小于5日均线的0.99并且价格小于昨收，但可以买回。
		elif A.stock[i] in holdings and holdings[A.stock[i]][1] > 0 and A.stock[i] not in orders_sell:
			if tick_price < 0.99 * current_line5 and tick_price < close_list[-2]:
				passorder(A.sell_code, 1101, A.acct, A.stock[i], 7, -1, holdings[A.stock[i]][1], 'test',1 , C)

		#重新买入条件：价格超5日均线的1.01
		elif A.amount < available_cash and A.stock[i] in holdings and holdings[A.stock[i]][0] == 0 and A.stock[i] not in orders_buy and A.stock[i] in orders_sell:  
			if tick_price >= 1.01 * current_line5 and current_line5 != 0: 
				passorder(A.buy_code, 1101, A.acct, A.stock[i], 0, -1, vol, 1 , C)
				#winsound.Beep(500,950)

		#买单，但一直有没成交
		elif A.stock[i] in orders_buy and orders_buy[A.stock[i]][0] > 0:  
			time_now = datetime.datetime.strptime(now_time, "%H%M%S")
			time_buy = datetime.datetime.strptime(orders_buy[A.stock[i]][2], "%H%M%S")
			time_1100 = datetime.datetime.strptime("110000", "%H%M%S")
			time_1130 = datetime.datetime.strptime("113000", "%H%M%S")
			diff = time_now - time_buy
			if time_now > time_1100 and time_now <= time_1130:   #在11点到11点30
				if diff.total_seconds() > 7200:
					if can_cancel_order(orders_buy[A.stock[i]][1],A.acct,A.acct_type):
						cancel(orders_buy[A.stock[i]][1], A.acct,A.acct_type, C)
			else:
				if diff.total_seconds() > 1800:
					if can_cancel_order(orders_buy[A.stock[i]][1],A.acct,A.acct_type):
						cancel(orders_buy[A.stock[i]][1], A.acct,A.acct_type, C)

		#卖单，但一直有没成交，取消后重新按买5买
		elif A.stock[i] in orders_sell and orders_sell[A.stock[i]][0] > 0 and A.stock[i] in holdings and holdings[A.stock[i]][1] > 0: 
			if orders_sell[A.stock[i]][3] == 0 : #没撤过
				time_now = datetime.datetime.strptime(now_time, "%H%M%S")
				time_buy = datetime.datetime.strptime(orders_sell[A.stock[i]][2], "%H%M%S")
				time_1120 = datetime.datetime.strptime("112000", "%H%M%S")
				time_1130 = datetime.datetime.strptime("113000", "%H%M%S")
				diff = time_now - time_buy
				if time_now > time_1120 and time_now <= time_1130:   #在11点20到11点30
					if diff.total_seconds() > 6000:   #除去休息的，过了十分钟以上
						if can_cancel_order(orders_sell[A.stock[i]][1],A.acct,A.acct_type):
							cancel(orders_sell[A.stock[i]][1], A.acct,A.acct_type, C)
							if tick_price < 0.99 * current_line5:
								passorder(A.sell_code, 1101, A.acct, A.stock[i], 7, -1, orders_sell[A.stock[i]][0], 1 , C)
				else:
					if diff.total_seconds() > 600:
						if can_cancel_order(orders_sell[A.stock[i]][1],A.acct,A.acct_type):
							cancel(orders_sell[A.stock[i]][1], A.acct,A.acct_type, C)
							if tick_price < 0.99 * current_line5:
								passorder(A.sell_code, 1101, A.acct, A.stock[i], 7, -1, orders_sell[A.stock[i]][0], 1 , C)
								#winsound.Beep(500,950)
			else:  #撤过，但还有委托剩余量，并且没有十分钟后卖掉
				if tick_price < 0.99 * current_line5:
					passorder(A.sell_code, 1101, A.acct, A.stock[i], 7, -1, orders_sell[A.stock[i]][0], 1 , C)