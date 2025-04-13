import json

class XTBMarket:
	"""
	Class responsible for retrieving market-relat data from the XTB API.
	Includes methods for symbols, balance, and margin calculations.
	"""
	def __init__(self, send_callback):
		"""
		Args:
			send_callback (function): Function to send messages over WebSocket.
		"""
		self.send = send_callback

	def get_all_symbols(self):
		"""
		Retrieve all tradable symbols from the broker.

		Returns: 
			dict: Full JSON response with symbol data.
		"""
		payload = {
			"command": "getAllSymbols"
		}
		result_data = json.loads(self.send(json_dumps(payload)))
		return result_data

	def get_symbol(self, symbol):
		"""
		Get detailed information for a specific trading symbol.

		Args:
			symbol (str): The symbol name (e.g. "AAPL")

		Returns: 
			dickt: Symbol data.
		"""
		payload = {
			"command": "getSymbol",
			"arguments": {
				"symbol": symbol
			}
		}
		result_data = json.loads(self.send(json_dumps(payload)))
		return result_data["returnData"]

	def get_balance(self):
		"""
		Retrieve curent account balance.

		Returns: 
			float: Account balance.
		"""
		payload = {
			"command": "getMarginLevel"
		}
		result_data = json.loads(self.send(json_dumps(payload)))
		return result_data["returnData"]["balance"]

	def get_margin(self, symbol, volume):
		"""
		Calculate margin requirement for a given trade.

		Args: 
			symbol (str): The trading symbol.
			volume (float): Volume to be traded.

		Returns: 
			float: Required margin.
		"""
		payload = {
			"command": "getMarginTrade",
			"arguments": {
				"symbol": symbol,
				"volume": volume
			}
		}
		result_data = json.loads(self.send(json_dumps(payload)))
		return result_data["returnData"]["margin"]
