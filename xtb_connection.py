"""Module containing connection facing methods"""
import json
import websocket
from xtb_utils import XtbUtils

class XtbConnectivity:
	"""Class that has methods facing connection"""
	def __init__(self, user_id, user_pswd):
		self.user_id = user_id
		self.user_pswd = user_pswd
		self.ws = None
		self.get_time = XtbUtils.get_time(self)
		self.exec_start = self.get_time

	def login(self):
		"""
		Login method to login to XTB API.

		Returns: True is successful or False if not
		"""
		payload ={
			"command": "login",
			"arguments": {
				"userId": self.user_id,
				"password": self.user_pswd
			}
		}
		result = json.loads(self.send_payload(json.dumps(payload)))
		status = result["status"]
		if str(status) == "True":
			return True
		raise ConnectionRefusedError(result['errorDescr'])

	def logout(self):
		"""Logout method to logout of XTB API.

		Returns: True is successful or False if not
		"""
		payload ={
			"command": "logout"
		}
		result = json.loads(self.send_payload(json.dumps(payload)))
		status = result["status"]
		self.disconnect()
		if str(status) == "True":
			return True
		return False

	def connect(self):
		"""
		Connect to the WebSocket server.

		Returns: 
			bool: True if connected successfully, False otherwise.
		"""
		try:
			self.ws=websocket.create_connection("wss://ws.xapi.pro/demo")
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

	def send_payload(self, msg):
		"""Method that sends a message to the websocket.

		Returns: result from websocket
		"""
		self.is_on()
		self.ws.send(msg)
		result = self.ws.recv()
		return result+"\n"

	def is_on(self):
		"""Method that checks if ??? is on.
		"""
		temp = (self.get_time - self.exec_start).total_seconds()
		if temp >= 8.0:
			self.connect()
		self.exec_start = self.get_time
