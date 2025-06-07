"""A wrapper for the xtb api"""
import json
from datetime import datetime, timedelta
from xtb_connection import XTB_connectivity 
from xtb_utils import XTB_utils
from xtb_account import XTB_account
from xtb_market import XTB_market
from xtb_trade import XTB_trade

class XTB:
	"""Class XTB that contains all the methods neccessary to use the api"""
	__version__ = "2.0"

	def __init__(self, user_id, user_pswd):
		self.user_id = user_id
		self.user_pswd = user_pswd
		self.connectivity = XTB_connectivity(self.user_id, self.user_pswd)
		send_callback = self.connectivity.send_payload
		self.utils = XTB_utils(send_callback)
		self.exec_start = self.utils.get_time()
		self.account = XTB_account(send_callback)
		self.market = XTB_market(send_callback)
		self.trade = XTB_trade(send_callback)

	def start(self):
		self.connectivity.connect()
		self.connectivity.login()

	def stop(self):
		self.connectivity.logout()
		self.connectivity.disconnect()
