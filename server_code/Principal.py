import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime as dt
from typing import Union, Literal, Optional

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
# @anvil.server.callable
# def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
#
class Loan:
	def __init__(self, loan_id):
		self.loan_id = loan_id 			#assigned by the database
		self.currency = Currency()
		
class EventParams:
	def __init__(self, 
							date: Optional[dt.date] = None, 
							time: Optional[dt.time] = None
							):
		self.loan_id:			Union[int, None] = 0	#fetch from the database	
		self.event_id:		Union[int, None] = 0	#assigned by the database
		self.event_date:	Optional[dt.date]= date if date else dt.now().date()
		self.event_time:	Optional[dt.timetz] = time if time else dt.now().timetz()
		self.event_beggining_date:	Optional[dt.date] = date if date else dt.now().date()
		self.event_ending_date:			Optional[dt.date] = date if date else dt.now().date()
		@property
		def event_days(self):
			return (self.event_ending_date - self.event_beggining_date).days
		self.event_name:	Optional[Literal["Principal lending", 
																		"Repayment", 
																		"Interest rate change",
																		"Capitalization",
																		"Principal balance correction",
																		"Interest balance correction",
																		"Leap year switch"]] = None
		self.event_type:	Literal["User input", "Automated"] = None

class Currency:
	def __init__(self, 
				ticker = None, 
				name = None, 
				rate = None, 
				currency_sum = 0):
		self.name = "Great Britain pounds"
		self.ticker = "GBP"
		self.rate = 1
		self.sum = currency_sum
		
class PrincipalLending(EventParams):
	def __init__(self, principal_lending_sum = None):
		super().__init__()
		self.currency = Currency(currency_sum = principal_lending_sum)
		self.event_name = "Principal lending"
		self.event_type = "User input"
		self.principal_lending_sum = 0
	@property
	def sum(self):
		return self.currency.rate * self.currency.sum

class Repayment(EventParams):
	def __init__(self, repayment_sum = None):
		super().__init__()
		self.repayment_sum = 0
		self.event_name = "Repayment"
		self.event_type = "User input"

Lending_1 = PrincipalLending(principal_lending_sum = 300000)
print(Lending_1.event_type)