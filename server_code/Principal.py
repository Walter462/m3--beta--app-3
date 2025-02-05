import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime as dt

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



class Event:
	def __init__(self, date  =None):
		self.date  = date if date else dt.now()
		self.id = 0
		self.inrest_acrrued = 0
		self.principal_balance = 0
		self.interest_balance = 0
		self.loan_balance = 0

class Loan:
	def __init__(self, loan_id):
		self.loan_id = loan_id
		self.currency = Currency()

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
		
class PrincipalLending:
	def __init__(self, 
				date = None,
				loan_id = None,
				principal_lending_sum = None):
		self.loan_id = loan_id
		self.currency = Currency(currency_sum = principal_lending_sum)
		self.principal_lending_sum = 0
		self.date = date if date else dt.now()
	@property
	def sum(self):
		return self.currency.rate * self.currency.sum

class Repayment(Event):
	def __init__(self, repayment_sum = None):
		super().__init__()
		self.repayment_sum = 0

#usd_currency = Currency()
Lending_1 = PrincipalLending("2024-01-10", loan_id = 1, principal_lending_sum = 300000)
Lending_2 = PrincipalLending("2024-01-20", loan_id = 1, principal_lending_sum = 44000)
Lending_2.currency.ticker = "USD"
Lending_2.currency.rate = 0.8065
paid = Repayment()

events_list = [Lending_1, Lending_2, paid]

for i in events_list:
	print(i.date)
	print((type(i.date)))


