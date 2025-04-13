from datetime import datetime, timedelta

class XTBUtils:
	"""
	Utility methods for time handling, connectivity checks, and conversions for XTB API operations.
	"""
	def __init__(self, get_server_time_callback, get_candles_callback):
		"""
		Args:
			get_server_time_callback (function): Function to get server time.
			get_candles_callback (function): Function to retrieve candles.
		"""
		self.get_server_time = get_server_time_callback
		self.get_candles = get_candles_callback
		self.exec_start = self.get_time()

	def to_milliseconds(self, days=0, hours=0, minutes=0):
		"""
		Convert time duration to milliseconds.

		Returns: 
			int: Time in milliseconds.
		"""
		milliseconds = (days*24*60*60*1000)+(hours*60*60*1000)+(minutes*60*1000)
		return milliseconds

	def get_time(self):
		"""
		Get current local time as datetime object.

		Returns: 
			datetime: Current time.
		"""
		now = datetime.today()
		return datetime.strptime(now.strftime('%m/%d/%Y %H:%M:%S%f'), '%m/%d/%Y %H:%M:%S%f')

	def time_conversion(self, date_str):
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
			symbol (str): Ticker symbol.

		Returns: 
			bool: True if market is open, False otherwise.
		"""
		candles = self.get_candles("M1", symbol, qty_candles=1)
		return len(candles) > 1

	def ping(self):
		"""
		Ping the XTB WebSocket connection.

		Returns:
			bool: True if the server is responsive.
		"""
		payload = {
			"command": "ping"
		}

		try:
			result_data = json.loads(self.api.connection.send(json_dumps(payload)))
			return result_data["status"] is True
		except (json.JSONDecodeError, KeyError, TypeError) as e:
			print(f"Ping failed: {e}")
			return False

	def get_server_time(self):
		"""Method that runs command getSeverTime.

		Returns: time
		"""
		payload = {
			"command": "getServerTime"
		}
		result_data = json.loads(self.send(json.dumps(payload)))
		server_time = result_data["returnData"]["time"]
		return server_time
