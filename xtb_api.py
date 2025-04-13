"""A wrapper for the xtb api"""
from xtb_connection_manager import XTBConnectionManager
from xtb_auth import XTBAuth
from xtb_market import XTBMarket
from xtb_trade import XTBTrade
from xtb_history import XTBHistory
from xtb_utils import XTBUtils

class XTB:
	"""Class XTB that contains all the methods neccessary to use the api"""
	__version__ = "2.0"

	def __init__(self, user_id, user_pswd):
		self.connection = XTBConnectionManager()
		self.connection.connect()

		send_callback = self.connection.send

		self.auth = XTBAuth(api=self)
		self.market = XTBMarket(send_callback)
		self.trade = XTBTrade(send_callback)
		self.history = XTBHistory(send_callback)
		self.utils = XTBUtils()

		self.user_id = user_id
		self.user_pswd = user_pswd

		self.auth.login(user_id=self.user_id, password=self.user_pswd)

		self.connection.disconnect()
