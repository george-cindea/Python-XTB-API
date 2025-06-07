import json

class XtbAccount:
	"""Class that hass methods facing the account"""

	def __init__(self, send_callback):
		self.send = send_callback

	def get_balance(self):
		"""Allows to get actual account indicators values in real-time, 
		as soon as they are available in the system.

		Returns: 
			float: Account balance
		"""
		payload = {
			"command": "getBalance"
		}
		result = json.loads(self.send(json.dumps(payload)))
		balance = result["returnData"]["balance"]
		return balance

	def mockup_1(self):
		"""Mockup method"""
		pass

	def mockup_2(self):
		"""Mockup method"""
		pass
