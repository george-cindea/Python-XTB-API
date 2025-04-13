import json

class XTBAuth:
	def __init__(self, api):
		self.api = api

	def login(self):
		"""
		Authenticate the user via XTB API.

		Returns: 
			bool: True if login successful, False otherwise.
		"""
		payload = {
			"command": "login",
			"arguments": {
				"userId": self.user_id,
				"password": self.user_pswd
			}
		}

		try:
			result_data = json.loads(self.api.connection.send(json.dumps(payload)))
			return result_data.get("status") is True
		except (KeyError, json.JSONDecodeError, TypeError) as e:
			print(f"Login failed due to unexpected response format: {e}")
			return False

	def logout(self):
		"""
		Logout the user via XTB API.

		Returns: 
			bool: True if logout successful, False otherwise.
		"""
		payload = {
			"command": "logout"
		}

		try:
			result_data = json.loads(self.api.connection.send(json.dumps(payload)))
			success = result_data.get("status") is True
		except (json.JSONDecodeError, KeyError, TypeError) as e:
			print(f"Logout failed: {e}")
			return False
		finally:
			self.disconnect()

		return success
