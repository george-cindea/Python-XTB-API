import websocket
import json
from datetime import datetime

class XTBConnectionManager:
	def __init__(self, url="wss://ws.xapi.pro/demo"):
		self.url = url
		self.ws = None
		self.exec_start = self.get_time()
		self.connect()

	def connect(self):
		"""
		Connect to the WebSocket server.

		Returns: 
			bool: True if connected successfully, False otherwise.
		"""
		try:
			self.ws=websocket.create_connection(self.url)
			return True
		except (websocket.WebSocketException) as e:
			print(f"Websocket connection failed: {e}")
			return False

	def disconnect(self):
		"""
		Disconnect from the WebSocket server.

		Returns: 
			bool: True if disconnected successfully, False otherwise.
		"""
		try:
			self.ws.close()
			return True
		except (websocket.WebSocketException) as e:
			print(f"Websocket disconnection failed: {e}")
			return False

	def send(self, msg):
		"""Method that sends a message to the websocket.

		Returns: result from websocket
		"""
		self.is_on()
		self.ws.send(msg)
		return self.ws.recv() + "\n"

	def is_on(self):
		"""Method that checks if ??? is on.
		"""
		temp = (self.get_time() - self.exec_start).total_seconds()
		if temp >= 8.0:
			self.connect()
		self.exec_start = self.get_time()

	def get_time(self):
		return datetime.today()
