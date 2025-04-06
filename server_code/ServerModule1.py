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
def add_loan(new_loan):
  for k,v in new_loan.items():
    print(k,v)
  #app_tables.loans.add_row(**kwargs)

@anvil.server.callable
def fetch_loan_info():
  return app_tables.loans.search()[0]

@anvil.server.callable
def fetch_companies_dropdown():
  return [(company['company_name'], company) for company in app_tables.companies.search()]

@anvil.server.callable
def fetch_companies():
  return app_tables.companies.search()

@anvil.server.callable
def fetch_user_info():
  user_info_keys= ['email', 'signed_up']
  user_info = {key: dict(anvil.users.get_user())[key] for key in user_info_keys}
  user_info['signed_up'] = user_info['signed_up'].date().strftime('%Y-%m-%d')
  return user_info

@anvil.server.callable
def fetch_subscriptions():
  current_user = anvil.users.get_user()
  subscription = [dict(r) for r in app_tables.subscription_admin.search(user=current_user)]
  subscriptions = [ ] 
  for s in subscription:
    sub_copy = dict(s.get('subscription')).copy()
    if 'created_on' in sub_copy and isinstance(sub_copy['created_on'], datetime):
      sub_copy['created_on'] = sub_copy['created_on'].strftime('%Y-%m-%d')
    subscriptions.append(sub_copy)
  return subscriptions
  
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
def add_loan1(lender,
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
  