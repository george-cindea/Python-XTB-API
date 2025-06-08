"""Module containing utilities methods"""
import json
from datetime import datetime

class XtbUtils:
	"""Class that has utility methods"""
	def __init__(self, send_callback):
		self.send = send_callback

	def ping(self):
		"""
		Regularly calling this function is enough to refresh the internal 
		state of all thecomponents in the system. 
		It is recommended that any application that does not execute other commands, 
		should call this command at least once every 10 minutes. 
		Please note that the streamingcounterpart of this function is 
		combination of "ping" and "getKeepAlive".

		Returns: 
			bool: True if the server is responsive
		"""
		payload = {
			"command": "ping"
		}
		try:
			result = json.loads(self.send(json.dumps(payload)))
			return result["status"] is True
		except (json.JSONDecodeError, KeyError, TypeError) as e:
			print(f"Ping command failed: {e}")
			return False

	@staticmethod
	def get_time():
		"""
		Get current local time as datetime object.

		Returns: 
			datetime: Current time.
		"""
		now = datetime.today()
		return datetime.strptime(now.strftime('%m/%d/%Y %H:%M:%S%f'), '%m/%d/%Y %H:%M:%S%f')

	@staticmethod
	def to_milliseconds(days=0, hours=0, minutes=0):
		"""
		Convert time duration to miliseconds.

		Returns: 
			int: Time in milliseconds.
		"""
		milliseconds = (days*24*60*60*1000)+(hours*60*60*1000)+(minutes*60*1000)
		return milliseconds

	@staticmethod
	def time_conversion(date_str):
		"""
		Convert date string to milliseconds since Unix epoch.

		Args:
			date_str (str): A datetime string in '%m/%d/%Y %H:%M:%S' format.

		Returns:
			int: Milliseconds since 1970-01-01 UTC.
		"""
		try:
			dt = datetime.strptime(date_str, '%m/%d/%Y %H:%M:%S')
			epoch = datetime(1970, 1, 1)
			delta = dt - epoch
			return int(delta.total_seconds() * 1000) #Return as milliseconds
		except ValueError as e:
			raise ValueError(f"Invalid date format: {date_str}. Expected MM/DD/YYYY HH:MM:SS") from e

	def is_open(self, symbol):
		"""
		Check if market is open for a symbol by testing candle data.

		Args:
			symbol (str) - Ticker symbol

		Returns: 
			bool: True if market is open, False otherwise.
		"""
		candles = self.get_candles("M1", symbol, qty_candles=1)
		return len(candles) > 1

	def get_server_time(self, data_type="int"):
		"""
		Returns current time on trading server.

		Returns: 
			int: Time
			str: Time described in form set on server (local time of server)
		"""
		payload = {
			"command": "getServerTime"
		}
		result = json.loads(self.send(json.dumps(payload)))
		server_time_int = result["returnData"]["time"]
		server_time_str = result["returnData"]["timeString"]
		return server_time_int if data_type == "int" else server_time_str
