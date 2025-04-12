"""A wrapper for the xtb api"""
import json
from datetime import datetime, timedelta
import websocket

class XTB:
	"""Class XTB that contains all the methods neccessary to use the api"""
	__version__ = "2.0"

	def __init__(self, user_id, user_pswd):
		self.user_id = user_id
		self.user_pswd = user_pswd
		self.ws = 0
		self.exec_start = self.get_time()
		self.connect()
		self.login()

	################ XTB ####################

	def login(self):
		"""
		Login method to login to XTB API.

		Returns: True is successful or False if not
		"""
		login ={
			"command": "login",
			"arguments": {
				"userId": self.user_id,
				"password": self.user_pswd
			}
		}
		login_json = json.dumps(login)
		#Sending Login Request
		result = self.send(login_json)
		result = json.loads(result)
		status = result["status"]
		if str(status)=="True":
			#Success
			return True
		#Error
		return False

	def logout(self):
		"""Logout method to logout of XTB API.

		Returns: True is successful or False if not
		"""
		logout ={
			"command": "logout"
		}
		logout_json = json.dumps(logout)
		#Sending Logout Request
		result = self.send(logout_json)
		result = json.loads(result)
		status = result["status"]
		self.disconnect()
		if str(status)=="True":
			#Success
			return True
		#Error
		return False

	def get_all_symbols(self):
		"""Method that executes getAllSymbols command.

		Returns: json object with all symbols and their data.
		"""
		allsymbols ={
			"command": "getAllSymbols"
		}
		allsymbols_json = json.dumps(allsymbols)
		result = self.send(allsymbols_json)
		result = json.loads(result)
		return result

	def get_candles(self, period, symbol, timeframe = None, qty_candles = 0):
		"""Get candle data for a symbol and specific period.

		Args:
			period (str): Timeframe string line 'M1', 'H1', 'D1', etc.
			symbol (str): Ticker/Symbol to retrieve candles for.
			timeframe (dict): Optional. Dict with keys 'days', 'hours', 'minutes'. Time window offset.
			qty_candles (int): Desired number of candles. If 0, fetch all.

		Returns: list[dict] or bool: Candle data, or False if none found.
		"""

		timeframe = timeframe or {}
		period_minutes = self._resolve_period_minutes(period)
		minutes = self._resolve_start_from_qty_or_days(
			timeframe = timeframe,
			period_minutes = period_minutes,
			qty_candles = qty_candles
		)

		start_timestamp = self.get_server_time() - self.to_milliseconds(
			days=timeframe.get("days", 0),
			hours=timeframe.get("hours", 0),
			minutes=minutes
		)

		payload = self._prepare_candle_payload(symbol, period_minutes, start_timestamp)
		response_data = json.loads(self.send(json.dumps(payload)))

		return self._parse_candle_response(response_data, qty_candles)

	def _resolve_start_from_qty_or_days(self, timeframe, period_minutes, qty_candles):
		"""Calculate extra minutes to look back based on quantity or provided minutes/hours."""
		base_minutes = timeframe.get("minutes", 0)
		base_hours = timeframe.get("hours", 0)

		additional_minutes = qty_candles * period_minutes if qty_candles else 0

		if qty_candles:
			additional_minutes *= 2

		return base_minutes + (base_hours * 60) + additional_minutes

	def _prepare_candle_payload(self, symbol, period, start):
		"""Helper method that prepares candle payload."""
		return {
			"command": "getChartLastRequest",
			"arguments": {
				"info": {
					"period": period,
					"start": start,
					"symbol": symbol
				}
			}
		}

	def _parse_candle_response(self, data, qty_candles):
		"""Helper method that parses candle data."""
		rate_infos = data.get("returnData", {}).get("rateInfos", [])
		digits = data.get("returnData", {}).get("digits", 5)

		if not rate_infos:
			return False

		candles = [{"digits": digits, "qty_candles": qty_candles or len(rate_infos)}]
		start_index = max(0, len(rate_infos) - qty_candles) if qty_candles else 0

		for rate in rate_infos[start_index:]:
			candles.append({
				"datetime": rate["ctmString"],
				"open": rate["open"],
				"close": rate["close"],
				"high": rate["high"],
				"low": rate["low"]
			})

		return candles

	def get_candles_range(self, period, symbol, timeframe = None, qty_candles = 0):
		"""Get candle data for a symbol between a start and end period.

		Args:
			period (str): Timeframe string line 'M1', 'H1', 'D1', etc.
			symbol (str): Ticker/Symbol to retrieve candles for.
			timeframe (dict): Optional. Dict with keys 'start', 'end', 'days'.
			qty_candles (int): Number of candles to retrieve. 0 = fetch all.

		Returns: list[dict] or bool: Candle data, or False if none found.
		"""
		timeframe = timeframe or {}
		period_minutes = self._resolve_period_minutes(period)

		start, end = self._resolve_time_range(
			timeframe = timeframe,
			period_minutes = period_minutes,
			qty_candles = qty_candles
		)

		payload = self._prepare_chart_range_payload(
			symbol = symbol,
			period = period_minutes,
			start = self.time_conversion(start),
			end = self.time_conversion(end)
		)

		response_data = json.loads(self.send(json.dumps(payload)))
		return self._parse_candle_response(response_data, qty_candles)

	def _resolve_period_minutes(self, period):
		"""Helper method to resolve the period."""
		period_map = {
			"M1": 1,
			"M5": 5,
			"M15": 15,
			"M30": 30,
			"H1": 60,
			"H4": 240,
			"D1": 1440,
			"W1": 10080,
			"MN1": 43200,
		}
		if period not in period_map:
			raise ValueError(f"Unsupported period: {period}")
		return period_map[period]

	def _resolve_time_range(self, timeframe, period_minutes, qty_candles):
		"""Helper method to get time range."""
		start = timeframe.get("start", 0)
		end = timeframe.get("end", 0)
		days = timeframe.get("days", 0)

		if end == 0:
			end_dt = self.get_time()
			end_str = end_dt.strftime('%m/%d/%Y %H:%M:%S')
		else:
			end_str = end

		if start == 0:
			end_dt = datetime.strptime(end_str, '%m/%d/%Y %H:%M:%S')
			if qty_candles == 0:
				start_dt = end_dt - timedelta(days=days)
			else:
				start_dt = end_dt - timedelta(minutes=period_minutes * qty_candles)
			start_str = start_dt.strftime('%m/%d/%Y %H:%M:%S')
		else:
			start_str = start

		return start_str, end_str


	def _prepare_chart_range_payload(self, symbol, period, start, end):
		"""Helper method that prepares candle payload."""
		return {
			"command": "getChartRangeRequest",
			"arguments": {
				"info": {
					"symbol": symbol,
					"period": period,
					"start": start,
					"end": end,
					"ticks": 0
				}
			}
		}

	def get_server_time(self):
		"""Method that runs command getSeverTime.

		Returns: time
		"""
		time ={
			"command": "getServerTime"
		}
		time_json = json.dumps(time)
		result = self.send(time_json)
		result = json.loads(result)
		time = result["returnData"]["time"]
		return time

	def get_balance(self):
		"""Method that runs command getMarginLevel in order to get the account balance.

		Returns: balance
		"""
		balance ={
			"command": "getMarginLevel"
		}
		balance_json = json.dumps(balance)
		result = self.send(balance_json)
		result = json.loads(result)
		balance = result["returnData"]["balance"]
		return balance

	def get_margin(self, symbol, volume):
		"""Method that runs command getMarginTrade.
		Args: volume

		Returns: margin
		"""
		margin ={
			"command": "getMarginTrade",
			"arguments": {
				"symbol": symbol,
				"volume": volume
			}
		}
		margin_json = json.dumps(margin)
		result = self.send(margin_json)
		result = json.loads(result)
		margin = result["returnData"]["margin"]
		return margin

	def get_profit(self, prices, cmd_type, symbol, volume):
		"""
		Calculate profit from a trade using prices and transaction type.
		Args:
			prices (dict): Contains 'open' and 'close' price.
			cmd_type (str): Trade command, e.g. 'BUY', 'SELL_LIMIT', 'CREDIT'.
			symbol (str): Ticker symbol.
			volume (float): Volume of the trade.

		Returns: 
			float: Calculated profit.

		Raises:
			ValueError: If cmd_type is invalid or prices are incomplete.
		"""
		#Validate prices
		if "open" not in prices or "close" not in prices:
			raise ValueError("prices dictionary must contain 'open' and 'close' keys")
		
		#CMD name to code mapping
		cmd_map = {
			"BUY": 0,
			"SELL": 1,
			"BUY_LIMIT": 2,
			"SELL_LIMIT": 3,
			"BUY_STOP": 4,
			"SELL_STOP": 5,
			"BALANCE": 6,
			"CREDIT": 7
		}
		
		if cmd_type not in cmd_map:
			raise ValueError(f"Invalid cmd_type '{cmd_type}'. Must be one of {list(cmd_map.keys())}")
		
		payload ={
			"command": "getProfitCalculation",
			"arguments": {
				"closePrice": prices["close"],
				"cmd": cmd_map[cmd_type],
				"openPrice": prices["open"],
				"symbol": symbol,
				"volume": volume
			}
		}
		
		result = json.loads(self.send(json.dumps(payload)))
		return result["returnData"]["profit"]

	def get_symbol(self, symbol):
		"""Method that runs command getSymbol in order to get all data for a particular ticker.
		Args:
			symbol - Ticker you request data for.

		Returns: symbol
		"""
		symbol ={
			"command": "getSymbol",
			"arguments": {
				"symbol": symbol
			}
		}
		symbol_json = json.dumps(symbol)
		result = self.send(symbol_json)
		result = json.loads(result)
		symbol = result["returnData"]
		return symbol

	def make_trade(
		self,
		symbol,
		cmd,
		transaction_type,
		volume,
		comment="",
		order=0,
		sl=0,
		tp=0,
		days=0,
		hours=0,
		minutes=0
	):
		"""
		Method that runs command tradeTransaction in order to make a trade request.
		Args:
			format trade_trans_info:
				cmd				Number		Operation code
				customComment	String		The value the customer may provide in order to retrieve it later.
				expiration		Time		Pending order expiration time
				offset			Number		Trailing offset
				order			Number		0 or position number for closing/modifications
				price			Float		Trade price
				sl				Float		Stop loss
				symbol			String		Trade symbol
				tp				Floati		Take profit
				type			Number		Trade transaction type
				volume			Float		Trade volume

			values cmd:
				BUY			0	buy
				SELL		1	sell
				BUY_LIMIT	2	buy limit
				SELL_LIMIT	3	sell limit
				BUY_STOP	4	buy stop
				SELL_STOP	5	sell stop
				BALANCE		6	Read only. Used in getTradesHistory  for manager's deposit/withdrawal operations
								(profit>0 for deposit, profit<0 for withdrawal).
				CREDIT		7	Read only

			values transaction_type:
				OPEN		0	order open, used for opening orders
				PENDING		1	order pending, only used in the streaming getTrades  command
				CLOSE		2	order close
				MODIFY		3	order modify, only used in the tradeTransaction  command
				DELETE		4	order delete, only used in the tradeTransaction  command
		"""
		price = self.get_candles("M1",symbol,qty_candles=1)
		price = price[1]["open"]+price[1]["close"]

		delay = self.to_milliseconds(days=days, hours=hours, minutes=minutes)
		if delay==0:
			expiration = self.get_server_time() + self.to_milliseconds(minutes=1)
		else:
			expiration = self.get_server_time() + delay

		trade_trans_info = {
			"cmd": cmd,
			"customComment": comment,
			"expiration": expiration,
			"offset": -1,
			"order": order,
			"price": price,
			"sl": sl,
			"symbol": symbol,
			"tp": tp,
			"type": transaction_type,
			"volume": volume
		}
		trade = {
			"command": "tradeTransaction",
			"arguments": {
				"tradeTransInfo": trade_trans_info
			}
		}
		trade_json = json.dumps(trade)
		result = self.send(trade_json)
		result = json.loads(result)
		if result["status"] is True: #if checking for value True
			#success
			return True, result["returnData"]["order"]
		#error
		return False, 0

	def check_trade(self, order):
		"""Method that runs command tradeTransactionStatus.

		Returns: 
			status:
				ERROR		0	error
				PENDING		1	pending
				ACCEPTED	3	The transaction has been executed successfully
				REJECTED	4	The transaction has been rejected
		"""
		trade ={
			"command": "tradeTransactionStatus",
			"arguments": {
					"order": order
			}
		}
		trade_json = json.dumps(trade)
		result = self.send(trade_json)
		result = json.loads(result)
		status = result["returnData"]["requestStatus"]
		return status

	def get_history(self, start=0, end=0, days=0, hours=0, minutes=0):
		"""Method that runs command getTradesHistory.

		Returns: history
		"""
		if start!=0:
			start = self.time_conversion(start)
		if end!=0:
			end = self.time_conversion(end)

		if days!=0 or hours!=0 or minutes!=0:
			if end==0:
				end = self.get_server_time()
			start = end - self.to_milliseconds(days=days, hours=hours, minutes=minutes)

		history ={
			"command": "getTradesHistory",
			"arguments": {
					"end": end,
					"start": start
			}
		}
		history_json = json.dumps(history)
		result = self.send(history_json)
		result = json.loads(result)
		history = result["returnData"]
		return history

	def ping(self):
		"""Method that runs command ping.

		Returns: status result
		"""
		ping ={
			"command": "ping"
		}
		ping_json = json.dumps(ping)
		result = self.send(ping_json)
		result = json.loads(result)
		return result["status"]

	################ TIME/DATE/CONVERSIONS ####################

	def get_time(self):
		"""Method that gets current time in a specific format.

		Returns: time
		"""
		time = datetime.today().strftime('%m/%d/%Y %H:%M:%S%f')
		time = datetime.strptime(time, '%m/%d/%Y %H:%M:%S%f')
		return time

	def to_milliseconds(self, days=0, hours=0, minutes=0):
		"""Method that gets time in milliseconds.

		Returns: milliseconds
		"""
		milliseconds = (days*24*60*60*1000)+(hours*60*60*1000)+(minutes*60*1000)
		return milliseconds

	def time_conversion(self, date):
		"""Method that converts time and date to seconds.

		Returns: time
		"""
		start = "01/01/1970 00:00:00"
		start = datetime.strptime(start, '%m/%d/%Y %H:%M:%S')
		date = datetime.strptime(date, '%m/%d/%Y %H:%M:%S')
		final_date = date-start
		temp = str(final_date)
		temp1, temp2 = temp.split(", ")
		hours, minutes, seconds = temp2.split(":")
		days = final_date.days
		days = int(days)
		hours = int(hours)
		hours+=2
		minutes = int(minutes)
		seconds = int(seconds)
		time = (days*24*60*60*1000)+(hours*60*60*1000)+(minutes*60*1000)+(seconds*1000)
		return time

	################ CHECKS ####################

	def is_on(self):
		"""Method that checks if ??? is on.
		"""
		temp1 = self.exec_start
		temp2 = self.get_time()
		temp = temp2 - temp1
		temp = temp.total_seconds()
		temp = float(temp)
		if temp>=8.0:
			self.connect()
		self.exec_start = self.get_time()

	def is_open(self, symbol):
		"""Method that checks if market is open.
		Args:
			symbol - ticker to run the check against

		Returns: True if successful, False if not
		"""
		candles = self.get_candles("M1", symbol, qty_candles=1)
		if len(candles)==1:
			return False
		return True

	################ WEBSOCKETS ####################

	def connect(self):
		"""Method that connects to the websocket.

		Returns: True if successful, False if not
		"""
		try:
			#self.ws=websocket.create_connection("wss://ws.xtb.com/demo")
			self.ws=websocket.create_connection("wss://ws.xapi.pro/demo")
			#Success
			return True
		except:
			#Error
			return False

	def disconnect(self):
		"""Method that disconnects to the websocket.

		Returns: True if successful, False if not
		"""
		try:
			self.ws.close()
			#Success
			return True
		except:
			return False

	def send(self, msg):
		"""Method that sends a message to the websocket.

		Returns: result from websocket
		"""
		self.is_on()
		self.ws.send(msg)
		result = self.ws.recv()
		return result+"\n"
