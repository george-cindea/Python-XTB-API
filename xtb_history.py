import json
from datetime import datetime, timmedelta

class XTBHistory:
	"""
	Class responsible for historical data retrieval from XTB API.
	Includes candle data and trade history.
	"""
	def __init__(self, send.callback):
		"""
		Args:
			send_callback (function): Function to send messages over WebSocket.
		"""
		self.send = send_callback

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
		minutes = self._resolve_start_from_qty_or_days(timeframe, period_minutes, qty_candles)

		start_timestamp = self.get_server_time() - self.to_milliseconds(
			days=timeframe.get("days", 0),
			hours=timeframe.get("hours", 0),
			minutes=minutes
		)

		payload = self._prepare_candle_payload(symbol, period_minutes, start_timestamp)
		response_data = json.loads(self.send(json.dumps(payload)))

		return self._parse_candle_response(response_data, qty_candles)

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

		start, end = self._resolve_time_range(timeframe, period_minutes, qty_candles)

		payload = self._prepare_chart_range_payload(
			symbol = symbol,
			period = period_minutes,
			start = self.time_conversion(start),
			end = self.time_conversion(end)
		)

		response_data = json.loads(self.send(json.dumps(payload)))
		return self._parse_candle_response(response_data, qty_candles)

	def get_history(self, start=0, end=0, time_range=None):
		"""
		Retrieve historical trade data for a given time range.

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
			start = self.time_conversion(start)
		if end != 0:
			end = self.time_conversion(end)

		#If time range is provided but start/end are not fully set
		if any(time_range.values()):
			if end == 0:
				end = self.get_server_time()
			start = end - self.to_milliseconds(
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

	def _resolve_start_from_qty_or_days(self, timeframe, period_minutes, qty_candles):
		"""Calculate extra minutes to look back based on quantity or provided minutes/hours."""
		base_minutes = timeframe.get("minutes", 0)
		base_hours = timeframe.get("hours", 0)

		additional_minutes = qty_candles * period_minutes if qty_candles else 0

		if qty_candles:
			additional_minutes *= 2

		return base_minutes + (base_hours * 60) + additional_minutes

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
