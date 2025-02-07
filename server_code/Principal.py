import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime as dt
from typing import Union, Literal, Optional, Tuple

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
class Loan:
	def __init__(self, 
							loan_id, 
							currency_ticker = None):
		self.loan_id = loan_id 			#assigned by the database
		self.loan_currency_ticker = currency_ticker or "GBP"
		self.loan_events_list = []
		#self.sorted_loan_events_list = []
	def loan_events_list_method(self, events):
		self.loan_events_list = [event for event in events if event.loan_id == self.loan_id]
		#self.sorted_loan_events_list = sorted(loan_events_list, key=lambda x: x.event_date)
class EventTimeSchedule:
		def __init__(self):
			self.event_beggining_date:	Optional[dt.date] = None
			self.event_ending_date:			Optional[dt.date] = None
			@property
			def event_days_count(self):
				return (self.event_ending_date - self.event_beggining_date).days
class EventParams:
	def __init__(self,
							event_id: Optional[int] = None, 
							date: Optional[dt.date]  = None, 
							time: Optional[dt.timetz] = None):
		self.event_id:		Optional[int] = event_id	#Assigned by DB
		self.loan_id:			Optional[int] = 0	#Fetch from DB
		self.event_date = date or dt.now().date()
		self.event_time = time or dt.now().timetz()
		self.event_type:	Literal["User input", "Auto"] = None
		self.event_name:	Optional[Literal["Principal lending", 
																		"Repayment", 
																		"Interest rate change",
																		"Capitalization",
																		"Principal balance correction",
																		"Interest balance correction",
																		"Leap year switch"]] = None
class PrincipalLending(EventParams):
	def __init__(self, 
							principal_lending_currency_sum = None,
							event_currency_ticker = None,
							event_currency_to_loan_rate = None
              ):
		super().__init__()
		self.event_name = "Principal lending"
		self.event_type = "User input"
		self.principal_lending_currency_sum = principal_lending_currency_sum or 0
		self.event_currency_ticker = event_currency_ticker or "GBP"
		self.event_currency_to_loan_rate = event_currency_to_loan_rate or 1
	@property
	def principal_lending_sum(self): #convert to loan_currency
		return  self.principal_lending_currency_sum * self.event_currency_to_loan_rate
class Repayment(EventParams):
  def __init__(self, 
							repayment_currency_sum = None, 
              event_currency_ticker = None, 
              event_currency_to_loan_rate = None):
    super().__init__()
    self.event_name = "Repayment"
    self.event_type = "User input"
    self.repayment_currency_sum = repayment_currency_sum or 0
    self.event_currency_ticker = event_currency_ticker or "GBP"
    self.event_currency_to_loan_rate = event_currency_to_loan_rate or 1
  @property
  def repayment_sum(self):
    return self.repayment_currency_sum * self.event_currency_to_loan_rate


#Instantiate classes
Lending_1 = PrincipalLending(event_date = "2025-01-13", principal_lending_currency_sum = 300000)
Lending_1.loan_id = 1
Lending_2 = PrincipalLending(event_date = "2025-01-01", principal_lending_currency_sum = 330000)
Lending_1.loan_id = 1

Loan_1 = Loan(1)
Loan_1.loan_events_list_method([Lending_1, Lending_2])
print(i.event_date for i in Loan_1.loan_events_list)