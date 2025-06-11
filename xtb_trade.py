"""Module containing trading facing methods"""
import json
from xtb_utils import XtbUtils

class XtbTrade:
	"""Class that has methods facing trade"""
	def __init__(self, send_callback, market_obj):
		self.send = send_callback
		self.market = market_obj

	def get_margin_trade(self, symbol, volume):
		"""Returns expected margin for given instrument and volume. 
		The value is calculated asexpected margin value, and therefore might not be perfectly accurate.
		This only works with CFDs (symbols ending in .<country>_4, not with STCs.

		Args: 
			symbol (str): The trading symbol
			volume (float): Volume to be traded

		Returns: 
			float: Required margin
		"""
		payload = {
			"command": "getMarginTrade",
			"arguments": {
				"symbol": symbol,
				"volume": volume
			}
		}
		result = json.loads(self.send(json.dumps(payload)))
		margin_trade = result["returnData"]["margin"]
		return margin_trade

	def get_profit_calculation(self, prices, cmd_type, symbol, volume):
		"""
		Calculates estimated profit for given deal data.
		Should be used for calculator-like apps only. 
		Profit for opened transactions should be taken from server, due to 
		higher precision of servercalculation.

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

		payload = {
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

	def make_trade(self, symbol, trade_settings, time_settings, comment=""):
		"""
		Starts trade transaction. 
		tradeTransaction sends main transaction information to the server.
		(XTB disabled API trading so altough this method works ok and upon
		execution you get an order id, XTB server will never create the order) 

		Args:
			symbol (str): The symbol to trade.
			trade_settings (dict): {
				'cmd': int,
				'transaction_type': int,
				'volume': float,
				'order': int,
				'stop_loss': float,
				'take_profit': float
			}
			time_settings (dict): {
				'days': int,
				'hours': int,
				'minutes': int
			}
			comment (str): Optional trade comment.

		Returns:
			tuple[bool, int]: Success, Order ID if success else 0)
		"""
		price = self._get_latest_price(symbol)
		expiration = self._calculate_expiration(time_settings)

		trade_info = {
			"cmd": trade_settings.get("cmd", 0),
			"type": trade_settings.get("transaction_type", 0),
			"volume": trade_settings.get("volume", 0.01),
			"order": trade_settings.get("order", 0),
			"sl": trade_settings.get("stop_loss", 0),
			"tp": trade_settings.get("take_profit", 0),
			"symbol": symbol,
			"price": price,
			"expiration": expiration,
			"offset": -1,
			"customComment": comment
		}

		payload = {
			"command": "tradeTransaction",
			"arguments": {"tradeTransInfo": trade_info}
		}

		response = json.loads(self.send(json.dumps(payload)))
		return (True, response["returnData"]["order"]) if response.get("status") else (False, 0)

	def _get_latest_price(self, symbol):
		"""Get the latest open and close price from M1 candles."""
		candles = self.market.get_candles("M1", symbol, qty_candles=1)
		if not candles or len(candles) < 2:
			raise ValueError(f"No price data found for {symbol}")
		return candles[1]["open"] + candles[1]["close"]

	def _calculate_expiration(self, time_settings):
		"""Calculate expiration timestamp based on delay settings."""
		delay_ms = XtbUtils(self.send).to_milliseconds(
			days=time_settings.get("days", 0),
			hours=time_settings.get("hours", 0),
			minutes=time_settings.get("minutes", 0)
		)
		default_expiry = XtbUtils(self.send).to_milliseconds(minutes=1)
		return XtbUtils(self.send).get_server_time() + (delay_ms or default_expiry)

	def check_trade(self, order):
		"""Please note that this function can be usually replaced by its streaming equivalent 
		"getTradeStatus" which is the preferred way of retrieving transaction status data.
		Returns current transaction status. 
		At any time of transaction processing client might check the status of transaction on server side. 
		In order to do that client must provide unique order taken from "tradeTransaction" invocation.

		Returns: 
			status:
				ERROR		0	error
				PENDING		1	pending
				ACCEPTED	3	The transaction has been executed successfully
				REJECTED	4	The transaction has been rejected
		"""
		payload = {
			"command": "tradeTransactionStatus",
			"arguments": {
					"order": order
			}
		}
		result = json.loads(self.send(json.dumps(payload)))
		status = result["returnData"]["requestStatus"]
		return status

	def get_trades_history(self, start=0, end=0, time_range=None):
		"""
		Please note that this function can be usually replaced by its streaming equivalent 
		"getTrades" which is the preferred way of retrieving trades data.
		Returns array of user's trades which were closed within specified period of time.

		Args:
			start (int or str): Optional start timestamp or foormatted string.
			end (int or str): Optional end timestamp or formatted string.
			time_range (dict): Optional dictionary with 'days', 'hours', and 'minutes'.

		Returns:
			dict: Trade history data.
		"""
		time_range = time_range or {}

		#Convert string-formatted times to timestamps
		if start != 0:
			start = XtbUtils.time_conversion(start)
		if end != 0:
			end = XtbUtils.time_conversion(end)

		#If time range is provided but start/end are not fully set
		if any(time_range.values()):
			if end == 0:
				end = XtbUtils(self.send).get_server_time()
			start = end - XtbUtils(self.send).to_milliseconds(
				days=time_range.get("days", 0),
				hours=time_range.get("hours", 0),
				minutes=time_range.get("minutes", 0)
			)

		payload = {
			"command": "getTradesHistory",
			"arguments": {"start": start, "end": end}
		}

		response = json.loads(self.send(json.dumps(payload)))
		return response["returnData"]
