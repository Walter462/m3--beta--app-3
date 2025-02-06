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
#
class Loan:
	def __init__(self, loan_id):
		self.loan_id = loan_id 			#assigned by the database
		self.loan_currency = Currency()
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
							date: Optional[dt.date]  = None, 
							time: Optional[dt.timetz] =None):
		self.loan_id:			Optional[int] = 0	#Fetch from DB
		self.event_id:		Optional[int] = 0	#Assigned by DB
		self.event_date = date or dt.now().date()
		self.event_time = time or dt.now().timetz()
		self.event_type:	Literal["User input", "Automated"] = None
		self.event_name:	Optional[Literal["Principal lending", 
																		"Repayment", 
																		"Interest rate change",
																		"Capitalization",
																		"Principal balance correction",
																		"Interest balance correction",
																		"Leap year switch"]] = None

class Currency:
    def __init__(self, 
								 ticker: str ="GBP", 
								 name: str = "Great Britain pounds", 
								 rate: float =1.0, 
								 currency_sum: float =0.0):
        self.ticker = ticker
        self.name = name
        self.rate = rate
        self.sum = currency_sum
    def convert_to(self, target_currency):
        """Converts the current sum to another currency based on exchange rate."""
        return self.sum * target_currency.rate
    @staticmethod
    def fetch_from_db(ticker):
        """Simulated database fetch."""
        currency_data = {
            "GBP": ("Great Britain pounds", 1.0),
            "USD": ("US Dollar", 1.3),
            "EUR": ("Euro", 1.1),
        }
        name, rate = currency_data.get(ticker, ("Unknown", 1.0))
        return Currency(ticker, name, rate)
    def __str__(self):
        return f"{self.sum:.2f} {self.ticker} ({self.name})"

class PrincipalLending(EventParams):
	def __init__(self, 
							event_date: Optional[dt.date] = None,
							principal_lending_currency_sum = None):
		super().__init__()
		self.principal_lending_currency_sum = Currency(currency_sum = principal_lending_currency_sum)
		self.event_date = event_date
		self.event_name = "Principal lending"
		self.event_type = "User input"
	@property
	def principal_lending_sum(self): #convert to loan_currency
		return self.currency.rate * self.currency.sum

class Repayment(EventParams):
	def __init__(self, repayment_sum = None):
		super().__init__()
		self.repayment_sum = 0
		self.event_name = "Repayment"
		self.event_type = "User input"

Lending_1 = PrincipalLending(event_date = "2025-01-13", principal_lending_currency_sum = 300000)
Lending_1.loan_id = 1
Lending_2 = PrincipalLending(event_date = "2025-01-01", principal_lending_currency_sum = 330000)
Lending_1.loan_id = 1

Loan_1 = Loan(1)
Loan_1.loan_events_list_method([Lending_1, Lending_2])
print(i.event_date for i in Loan_1.loan_events_list)