import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime, timedelta, date
from uuid import uuid4
# Additional import
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Union, Literal, Any
from collections import defaultdict
from decimal import Decimal, getcontext, localcontext
import pandas as pd
import json
import warnings

'''
- [ ] STYLE(rename): principal_repayment_currency -> principal_currency_allocation
- [ ] STYLE(rename): interest_repayment_currency -> interest_currency_allocation
'''
#=====================
# 0. Remote connection
#=====================
def open_remote_connection():
    try:
        with open('config/uplink_config.json', 'r') as config_file:
            config = json.load(config_file)
            key = config.get('anvil_server_key')
            if key:
                anvil.server.connect(key)
    except FileNotFoundError:
        pass  # No config file? No problem — just skip connection.
open_remote_connection()

# Set global precision to 6 decimal places
getcontext().prec = 6
# ==============================
# 1. Define Data Classes
# ==============================
@dataclass
class Loan:
    loan_id: str
    base_currency: str
    interest_rate_base: Union[Literal[360, 365], Literal['calendar']] = 365
    lending_date_exclusive_counting: bool = False
    repayment_date_exclusive_counting: bool = True
    capitalization: bool = False
    # Additional fields from the loan data
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    lender: Optional[Any] = None
    borrower: Optional[Any] = None
    created_on: Optional[datetime] = None
    updated: Optional[datetime] = None
    credentials: Optional[str] = None
    archived: bool = False
    interest_rate_type: Optional[str] = None
    capitalization_dates: Optional[Any] = None

@dataclass
class Currency:
    currency_amount: Decimal
    ticker: str
    currency_to_loan_rate: Decimal = Decimal('1.0')  # Conversion rate to loan currency
    def converted_amount(self) -> Decimal:
        return self.currency_amount * self.currency_to_loan_rate

@dataclass
class Event:
    '''
    Populated with None values for safety reasons.
    Default values do not make effect as they should be overwritten (None or input for each event in the event class builder loop (.:89-149)
    '''
    loan: Optional[Loan] = None
    event_fact_date: Optional[datetime] = None
    event_start_date: Optional[datetime] = None
    event_id: Optional[int] = None
    principal_lending_currency: Optional[Currency] = None
    principal_lending: Optional[Decimal] = None
    capitalization: Decimal = None
    interest_rate: Optional[Decimal] = None
    interest_rate_base: Decimal = None

    principal_repayment_currency: Optional[Currency] = None
    principal_repayment: Optional[Decimal] = None
    interest_repayment_currency: Optional[Currency] = None
    interest_repayment: Optional[Decimal] = None

    principal_balance_correction: Optional[Decimal] = None
    interest_balance_correction: Optional[Decimal] = None

@dataclass
class AggregatedEvent:
    '''
    Assign default values to Decimal('0.0') at aggregation stage (.:173-195) if values not provided.
    Avoids NoneType errors when performing balance calculations (:248).
    '''
    loan: Loan
    event_fact_date: datetime
    event_start_date: Optional[datetime]
    event_end_date: Optional[datetime] = None
    days_count: int = 0
    event_ids: List[int] = field(default_factory=list)
    principal_lending_currency: Currency = field(default_factory=lambda: Currency(currency_amount=Decimal('0.0'), ticker=None, currency_to_loan_rate=None))
    principal_lending: Decimal = Decimal('0.0')
    capitalization: Decimal = Decimal('0.0')
    interest_rate: Decimal = Decimal('0.0')
    interest_rate_base: Decimal = None

    principal_repayment_currency: Currency = field(default_factory=lambda: Currency(currency_amount=Decimal('0.0'), ticker=None, currency_to_loan_rate=None))
    principal_repayment: Decimal = Decimal('0.0')
    interest_repayment_currency: Currency = field(default_factory=lambda: Currency(currency_amount=Decimal('0.0'), ticker=None, currency_to_loan_rate=None))
    interest_repayment: Decimal = Decimal('0.0')

    principal_balance_correction: Decimal = Decimal('0.0')
    interest_balance_correction: Decimal = Decimal('0.0')
    principal_balance: Decimal = Decimal('0.0')
    interest_accrued: Decimal  = Decimal('0.0')
    interest_balance: Decimal  = Decimal ('0.0')

# ==============================
# 2. Fetch data (Loans, Events)
#============================
# 2.1. Loans
#============================
def fetch_raw_loan_info()->dict:
  '''
  Fetches raw loan data from the database.
  '''
  loans_list = [dict(app_tables.loans.search()[0])]
  return loans_list

def loans_dataclass_listing()->List[Loan]:
  '''
  Converts raw loan data to Loan dataclass instances.
  '''
  loans_list_raw = fetch_raw_loan_info()
  loans_dataclass_list = [Loan(**loan) for loan in loans_list_raw]
  return loans_dataclass_list

def loans_mapping(loans_dataclass_list) -> Dict[str, Loan]:
  '''
  Creates a dictionary mapping loan IDs to Loan dataclass instances.
  '''
  loans_mapping = {loan.loan_id: loan for loan in loans_dataclass_list}
  return loans_mapping


#============================
# 2.2. Events
#============================
def fetch_loan_events():
  '''
  Fetch loan events from the database.
  - Interest rates
  - Lendings
  - Repayments\n
  Returns a list of dictionaries with the combined event data.
  '''
  interest_rates = [{**dict(item), "event_type":"Interest rate", "loan_id":item['loan']['loan_id']} for item in
                    app_tables.interest_rates.search(loan=app_tables.loans.search()[0])]
  lendings = [{**dict(item), "event_type": "Lending", "loan_id":item['loan']['loan_id']} for item in 
              app_tables.principal_lendings.search(loan=app_tables.loans.search()[0])]
  repayments = [{**dict(item), "event_type": "Repayment", "loan_id":item['loan']['loan_id']} for item in 
                app_tables.repayments.search(loan=app_tables.loans.search()[0])]
  events_list_raw = interest_rates + lendings + repayments
  return events_list_raw


print(*[fetch_loan_events()], sep ="\n")

def events_dataclass_listing(events_list_raw)->List[Event]:
  loan_mapping = loans_mapping(loans_dataclass_listing())
  events_list = []
  for event in events_list_raw:
      loan = loan_mapping.get(event.get("loan_id"))
      if not loan:
          raise ValueError(f"Loan with ID {event.get('loan_id')} not found.")
      event_fact_date = event["event_fact_date"]
      event_start_date: Optional[datetime] = event_fact_date
      principal_lending_currency = None
      principal_lending = None

      principal_repayment_currency = None
      principal_repayment = None
      interest_repayment_currency = None
      interest_repayment = None

      capitalization = None
      interest_rate = None
      principal_balance_correction = None
      interest_balance_correction = None

      if "principal_lending_currency" in event:
          lending_date_exclusive_counting = loan.lending_date_exclusive_counting
          if event.get("currency") is None:
            warnings.warn(f"Currency is explicitly set to None for Event ID {event['event_id']}.\
                          Defaulting to loan base currency: {loan.base_currency}.", UserWarning)
          currency_ticker = event.get("currency") if event.get("currency") is not None else loan.base_currency # Event currency
          currency_rate = event.get("currency_to_loan_rate", None)  # Fetch conversion rate
          # If currencies are different but no conversion rate is provided, raise an error
          if currency_ticker != loan.base_currency and currency_rate is None:
              raise ValueError(
                  f"Missing currency conversion rate for Event ID {event['event_id']}: "
                  f"{currency_ticker} → {loan.base_currency}"
              )
          # Ensure currency_rate is Decimal, default to 1.0 if same currency
          currency_rate = Decimal(str(currency_rate)) if currency_rate is not None else Decimal('1.0')
          # Create Currency object
          principal_lending_currency = Currency(
              currency_amount=Decimal(event["principal_lending_currency"]),
              ticker=currency_ticker,
              currency_to_loan_rate=currency_rate
          )
          # Convert amount if necessary
          principal_lending = (
              principal_lending_currency.converted_amount()
              if currency_ticker != loan.base_currency
              else principal_lending_currency.currency_amount
          )
          if lending_date_exclusive_counting == True:
              event_start_date += timedelta(days=1)
          else:
            event_start_date = event_fact_date

      if "principal_repayment_currency" in event and (event.get("principal_repayment_currency") is not None 
                                                      and Decimal(event["principal_repayment_currency"]) >= 0):
          repayment_date_exclusive_counting = loan.repayment_date_exclusive_counting
          if event.get("currency") is None:
            warnings.warn(f"Currency is explicitly set to None for Event ID {event['event_id']}.\
                          Defaulting to loan base currency: {loan.base_currency}.", UserWarning)
          currency_ticker = event.get("currency") if event.get("currency") is not None else loan.base_currency # Event currency
          currency_rate = event.get("currency_to_loan_rate", None)  # Fetch conversion rate
          # If currencies are different but no conversion rate is provided, raise an error
          if currency_ticker != loan.base_currency and currency_rate is None:
              raise ValueError(
                  f"Missing currency conversion rate for Event ID {event['event_id']}: "
                  f"{currency_ticker} → {loan.base_currency}"
              )
          # Ensure currency_rate is Decimal, default to 1.0 if same currency
          currency_rate = Decimal(str(currency_rate)) if currency_rate is not None else Decimal('1.0')
          # Create Currency object
          principal_repayment_currency = Currency(
              currency_amount=Decimal(event["principal_repayment_currency"]),
              ticker=currency_ticker,
              currency_to_loan_rate=currency_rate
          )
          # Convert amount if necessary
          principal_repayment = (
              principal_repayment_currency.converted_amount()
              if currency_ticker != loan.base_currency
              else principal_repayment_currency.currency_amount
          )
          if repayment_date_exclusive_counting == True:
              event_start_date += timedelta(days=1)
          else:
            event_start_date = event_fact_date

      if "interest_repayment_currency" in event and (event.get("interest_repayment_currency") is not None 
                                                    and Decimal(event["interest_repayment_currency"]) >= 0):
          repayment_date_exclusive_counting = loan.repayment_date_exclusive_counting
          currency_ticker = event.get("currency") if event.get("currency") is not None else loan.base_currency # Event currency
          if currency_ticker is None:
            warnings.warn(f"Currency is explicitly set to None for Event ID {event['event_id']}.\
                          Defaulting to loan base currency: {loan.base_currency}.", UserWarning)
          currency_rate = event.get("currency_to_loan_rate", None)  # Fetch conversion rate
          # If currencies are different but no conversion rate is provided, raise an error
          if currency_ticker != loan.base_currency and currency_rate is None:
              raise ValueError(
                  f"Missing currency conversion rate for Event ID {event['event_id']}: "
                  f"{currency_ticker} → {loan.base_currency}"
              )
          # Ensure currency_rate is Decimal, default to 1.0 if same currency
          currency_rate = Decimal(str(currency_rate)) if currency_rate is not None else Decimal('1.0')
          # Create Currency object
          interest_repayment_currency = Currency(
              currency_amount=Decimal(event["interest_repayment_currency"]),
              ticker=currency_ticker,
              currency_to_loan_rate=currency_rate
          )
          # Convert amount if necessary
          interest_repayment = (
              interest_repayment_currency.converted_amount()
              if currency_ticker != loan.base_currency
              else interest_repayment_currency.currency_amount
          )
          if repayment_date_exclusive_counting == True:
              event_start_date += timedelta(days=1)
          else:
            event_start_date = event_fact_date
      
      if "capitalization" in event:
        capitalization=Decimal(event.get("capitalization"))
      if "interest_rate" in event:
        interest_rate=Decimal(event.get("interest_rate"))
      if "principal_balance_correction" in event:
        principal_balance_correction=Decimal(event.get("principal_balance_correction"))
      if "interest_balance_correction" in event:
        interest_balance_correction=Decimal(event.get("interest_balance_correction"))
      # Create the Event instance
      events_list.append(
          Event(
              event_id=event["event_id"],
              event_fact_date=event_fact_date,
              event_start_date = event_start_date,
              loan=loan,
              principal_lending_currency=principal_lending_currency,
              principal_lending = principal_lending,
              principal_repayment_currency = principal_repayment_currency,
              principal_repayment = principal_repayment,
              interest_repayment_currency = interest_repayment_currency,
              interest_repayment = interest_repayment,
              capitalization=capitalization,
              interest_rate=interest_rate,
              principal_balance_correction=principal_balance_correction,
              interest_balance_correction=interest_balance_correction
          )
      )
  return events_list

events_list = events_dataclass_listing(events_list_raw = fetch_loan_events())
events_list_sorted: List[Event] = sorted(events_list, key=lambda e: (e.event_start_date, e.event_id))

print(*events_list_sorted, sep="\n")
# After populating the Event instance

#for event in events_list_sorted:
#  print(f"Event ID: {event.event_fact_date}. {event.principal_lending_currency.currency_amount}")#, Principal Lending: {principal_lending}, Principal Repayment: {principal_repayment}, Interest Repayment: {interest_repayment}")



print("-" * 180)
print(f"{'Date':<12} {'Start event date':<12} {'Currency lending':>18} {'Currency':>10} {'Rate':>10} {'Principal lending':>18} {'Principal repayment':>18} {'Interest repayment':>18} {'Event IDs':>12}")
print("-" * 180)
for event in events_list_sorted:
    event_fact_date = str(event.event_fact_date)  # Ensure event_fact_date is a string
    event_start_date = str(event.event_start_date) 
    lending_amount = f"{event.principal_lending_currency.currency_amount:.2f}" if event.principal_lending_currency and event.principal_lending_currency.currency_amount is not None else ""
    lending_currency = event.principal_lending_currency.ticker if event.principal_lending_currency else ""
    currency_rate = f"{event.principal_lending_currency.currency_to_loan_rate:.4f}" if event.principal_lending_currency and event.principal_lending_currency.currency_to_loan_rate is not None else ""
    principal_lending = f"{event.principal_lending:.2f}" if event.principal_lending is not None else ""
    principal_repayment = f"{event.principal_repayment:.2f}" if event.principal_repayment is not None else ""
    interest_repayment = f"{event.interest_repayment:.2f}" if event.interest_repayment is not None else ""
    event_id = str(event.event_id) if event.event_id is not None else ""

    print(f"{event_fact_date:<12} {event_start_date:<12}{lending_amount:>18} {lending_currency:>10} {currency_rate:>10} {principal_lending:>18} {principal_repayment:>18} {interest_repayment:>18} {event_id:>12}")

print("-" * 180)


