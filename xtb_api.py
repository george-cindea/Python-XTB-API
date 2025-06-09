"""Wrapper for the xtb api"""
from xtb_connection import XtbConnectivity
from xtb_utils import XtbUtils
from xtb_account import XtbAccount
from xtb_market import XtbMarket
from xtb_trade import XtbTrade

class XTB:
	"""Class XTB that contains all the methods neccessary to use the api"""
	__version__ = "2.0"

	def __init__(self, user_id, user_pswd):
		self.user_id = user_id
		self.user_pswd = user_pswd
		self.connectivity = XtbConnectivity(self.user_id, self.user_pswd)
		self.send_callback = self.connectivity.send_payload
		self.utils = XtbUtils(self.send_callback)
		self.exec_start = XtbUtils.get_time()
		self.account = XtbAccount(self.send_callback)
		self.market = XtbMarket(self.send_callback)
		self.trade = XtbTrade(self.send_callback, self.market)

	def start(self):
		"""Connect and login"""
		self.connectivity.connect()
		self.connectivity.login()

	def stop(self):
		"""Logout and disconnect"""
		self.connectivity.logout()
		self.connectivity.disconnect()

	def mockup_1(self):
		"""Mockup method"""
