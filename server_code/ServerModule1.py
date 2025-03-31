import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime
from uuid import uuid4


# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
#@anvil.server.callable
#def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
@anvil.server.callable
def fetch_user_info():
  

@anvil.server.callable
def add_subscrition(Loan_DB_name):
  app_tables.subscription.add_row(
    created_on=datetime.now(),
    Loan_DB_profile_name=Loan_DB_name
  )

@anvil.server.callable
def get_interest_rate_bases():
  interest_rate_bases =['360', '365', 'calendar']
  return(interest_rate_bases)
  
@anvil.server.callable
def get_currency_ticker():
  currency_tickers =['USD', 'EUR', 'GBP', 'JPY']
  return(currency_tickers)

@anvil.server.callable
def add_loan(lender,
              borrower,
              description,
              base_currency,
              interest_rate_base,
              lending_date_exclusive_counting,
              repayment_date_exclusive_counting,
              capitalization):
  app_tables.loan.add_row(id=str(str(uuid4())),
                              created_on = datetime.now(),
                              lender = lender,
                              borrower = borrower,
                              description = description,
                              base_currency = base_currency,
                              interest_rate_base = interest_rate_base,
                              lending_date_exclusive_counting = lending_date_exclusive_counting,
                              repayment_date_exclusive_counting = repayment_date_exclusive_counting,
                              capitalization = capitalization)
  