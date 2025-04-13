import json

class XTBTrade:
	"""
	Handles trading operations through the XTB API such as opening trades,
	checking trade status, and calculating profit.
	"""
	def __init__(self, send_callback, get_candles_callback, get_server_time_callback, to_milliseconds_callback):
		"""
		Args:
			send_callback (function): Function to send messages via WebSocket.
			get_candles_callback (function): Function to fetch latest price info.
			get_server_time_callback (function): Function to retrieve current server time.
			to_milliseconds_callback (function): Function to convert time to milliseconds.
		"""
		self.send = send_callback
		self.get_candles = get_candles_callback
		self.get_server_time = get_server_time_callback
		self.to_milliseconds = to_milliseconds_callback

	def make_trade(self, symbol, trade_settings, time_settings, comment=""):
		"""
		Execute a trade via tradeTransaction command.

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
			raise ValueError("'prices' dictionary must contain 'open' and 'close' keys")

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

		result_data = json.loads(self.send(json.dumps(payload)))
		return result_data["returnData"]["profit"]

	def check_trade(self, order):
		"""
		Check the status of a trade.

		Args:
			order (int): Order ID to check.

		Returns: 
			int: Status code.
		"""
		payload = {
			"command": "tradeTransactionStatus",
			"arguments": {
				"order": order
			}
		}
		result_data = json.loads(self.send(json_dumps(payload)))
		return result_data["returnData"]["requestStatus"]

	def _get_latest_price(self, symbol):
		"""Get the latest open and close price from M1 candles."""
		candles = self.get_candles("M1", symbol, qty_candles=1)
		if not candles or len(candles) < 2:
			raise ValueError(f"No price data found for {symbol}")
		return candles[1]["open"] + candles[1]["close"]

	def _calculate_expiration(self, time_settings):
		"""Calculate expiration timestamp based on delay settings."""
		delay_ms = self.to_milliseconds(
			days=time_settings.get("days", 0),
			hours=time_settings.get("hours", 0),
			minutes=time_settings.get("minutes", 0)
		)
		default_expiry = self.to_milliseconds(minutes=1)
		return self.get_server_time() + (delay_ms or default_expiry)
