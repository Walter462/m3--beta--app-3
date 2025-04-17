import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime, timedelta
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
def delete_loan(loan):
  if app_tables.loans.has_row(loan):
    loan.delete()
  else:
    raise Exception("Loan does not exist")
    
@anvil.server.callable
def update_loan(loan, edited_loan):
  if app_tables.loans.has_row(loan):
    edited_loan['updated'] = datetime.now()
    loan.update(**edited_loan)
  else:
    raise Exception("Loan does not exist")

@anvil.server.callable
def add_loan(new_loan):
  app_tables.loans.add_row(
    loan_id=str(uuid4()),
    created_on = datetime.now(),
    **new_loan)

@anvil.server.callable
def fetch_loans_info():
  return app_tables.loans.search()

@anvil.server.callable
def fetch_companies_dropdown():
  return [(company['company_name'], company) for company in app_tables.companies.search()]

@anvil.server.callable
def clear_cookies():
  print(f"Cookie {anvil.server.cookies.local} cleared")
  return anvil.server.cookies.local.clear()

def companies_check(companies_data):
  for row in companies_data:
    if app_tables.companies.has_row(row) is False:
      print(f'Row {row} needs to be refreshed')
    else:
      print("Ok")

@anvil.server.callable
def fetch_companies():
  if anvil.server.cookies.local.get('companies', None) is not None:
    companies_cookie = anvil.server.cookies.local.get('companies')
    print(f'Found a cookie: {companies_cookie}')
    companies_check(companies_cookie)
    #return companies_cookie
  else:
    #companies_data = [dict(item) for item in app_tables.companies.search()]
    companies_cookie = [dict(row) for row in app_tables.companies.search()]
    anvil.server.cookies.local['companies'] = companies_cookie
    print(f"Fetching companies info from database: {anvil.server.cookies.local.get('companies')}")
    companies_check(companies_cookie)
    #return companies_data
      

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



# Unused section
"""
@anvil.server.callable
def fetch_loans_list_info():
  loan_info_keys = ['lender', 'borrower', 'contract_start_date', 'credentials']
  results = [ ]
  for item in app_tables.loans.search():
    loan_data = { }
    for key in loan_info_keys:
      value = item[key]
      if key in ['lender', 'borrower']:
        loan_data[key] =  item[key]['company_name'] if value else None
      elif key == 'contract_start_date':
        if value:
          loan_data[key] = value.strftime('%Y-%m-%d')
        else:
          loan_data[key] = None
      else:
        loan_data[key] = value
    results.append(loan_data)
  return results
"""