import anvil.google.auth, anvil.google.drive, anvil.google.mail
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.tables
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
#import logging
import logging
import Logging_config

'''
- [ ] STYLE(rename): principal_repayment_currency -> principal_currency_allocation
- [ ] STYLE(rename): interest_repayment_currency -> interest_currency_allocation
- [ ] REF: avoid unnecessary data sorting stages
- [ ] REV: date and datetime datatypes consistency
- [ ] FEAT(front): # DEBUG: print sorted List[Event] 390
- [ ] DEBUG: add logger
- [ ] DEBUG: add logger level(execution time tracking)
- [ ] FEAT: capitalization TRUE/FALSE handling in def loan_parameters_calculations():
'''
#=====================
# 0. Remote connection
#=====================
Logging_config.setup_logging()

#@Logging_config.execution_time_tracking
def open_remote_connection():
    try:
        with open('config/uplink_config.json', 'r') as config_file:
            config = json.load(config_file)
            key = config.get('anvil_server_key')
            if key:
                anvil.server.connect(key)
    except FileNotFoundError:
        pass  # No config file? No problem — just skip connection.
#open_remote_connection()

# Set global precision to 6 decimal places
getcontext().prec = 6
# ==============================
# 1. Define Data Classes
# ==============================
@dataclass
class Loan:
    '''
    Stores loan properties used for calculations and others. 
    Calculations properties:
    - loan_id
    - base_currency
    - interest_rate_base
    - lending_date_exclusive_counting
    - repayment_date_exclusive_counting
    - capitalization
    - capitalization_dates
    - interest_rate_type
    '''
    loan_id: str
    base_currency: str
    interest_rate_base: Union[Literal[360, 365], Literal['calendar']] = 365
    lending_date_exclusive_counting: bool = False
    repayment_date_exclusive_counting: bool = True
    capitalization: bool = False
    capitalization_dates: Optional[Any] = None
    interest_rate_type: Optional[str] = None
    # Additional fields from the loan data
    contract_start_date: Optional[date] = None
    contract_end_date: Optional[date] = None
    lender: Optional[Any] = None
    borrower: Optional[Any] = None
    created_on: Optional[datetime] = None
    updated: Optional[datetime] = None
    credentials: Optional[str] = None
    archived: bool = False

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
"""
class RawLoansListCache1:
  '''
  Loan data storage class. Helps caching to avoid multiple DB requests.
  - get_dicted_loans_list() - fetch loan data from cache or DB
  '''
  _instance = None
  _loans_cache = None
  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance
  def get_dicted_loans_list(self)->List[dict]:
    if self._loans_cache is None:
      # fetch a single loan
      self._loans_cache = [dict(app_tables.loans.search()[0])]
    return self._loans_cache
"""

class RawLoansListCache:
  '''
  Loan data storage class. Helps caching to avoid multiple DB requests.
  - cache_raw_loans_data() - fetch loan data from DB and save it in cache (Server RAM)
  - get_dicted_loans_list() - convert cached loan data to dict
  '''
  _instance = None
  _loans_cache = None
  _loans_cache_dicted = None
  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance
  def cache_raw_loans_data(self)->List[anvil.tables.Row]:
    if self._loans_cache is None:
      # fetch a single loan
      self._loans_cache = [app_tables.loans.search()[0]]
      return self._loans_cache
  def get_dicted_loans_list(self)->List[dict]:
    if self._loans_cache_dicted is None:
      # fetch a single loan
        raw_loans_data = self.cache_raw_loans_data()
        self._loans_cache_dicted = [dict(row) for row in raw_loans_data]
    return self._loans_cache_dicted

@Logging_config.execution_time_tracking
def fetch_raw_loan_info()->List[dict]:
  '''
  Fetches raw loan data from the database.
  Normally it is a single loan.
  '''
  #raw_loans_list = [dict(loan) for loan in RawLoansListCache().get_dicted_loans_list()]
  raw_loans_list = RawLoansListCache().get_dicted_loans_list()
  return raw_loans_list

def loans_dataclass_listing()->List[Loan]:
  '''
  Converts raw loan data to Loan dataclass instances list.
  '''
  loans_list_raw: List[dict]= fetch_raw_loan_info()
  loans_dataclass_list: List[Loan] = [Loan(**loan) for loan in loans_list_raw]
  return loans_dataclass_list

def loans_mapping() -> Dict[str, Loan]:
  '''
  Creates a dictionary mapping loan IDs to Loan dataclass instances.
  Useful in multiple loans statistics aggregated by company.
  '''
  loans_dataclass_list: List[Loan] = loans_dataclass_listing()
  loans_mapping = {loan.loan_id: loan for loan in loans_dataclass_list}
  return loans_mapping

#============================
# 2.2. Events
#============================
# DEBUG: Speed up debugging by RawEventsListCache class
class RawEventsListCache:
  _instance = None
  _events_cache = None
  def __new__(cls):
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance
  def get_events(self):
    if self._events_cache is None:
      interest_rates = [{**dict(item), "event_type":"Interest rate", "loan_id":item['loan']['loan_id']} for item in
                  app_tables.interest_rates.search(loan=app_tables.loans.search()[0])]
      lendings = [{**dict(item), "event_type": "Lending", "loan_id":item['loan']['loan_id']} for item in 
                  app_tables.principal_lendings.search(loan=app_tables.loans.search()[0])]
      repayments = [{**dict(item), "event_type": "Repayment", "loan_id":item['loan']['loan_id']} for item in 
                    app_tables.repayments.search(loan=app_tables.loans.search()[0])]
      raw_events_list = interest_rates + lendings + repayments
      self._events_cache = raw_events_list
    return self._events_cache
    
@Logging_config.execution_time_tracking
def fetch_loan_events()->List[dict]:
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
  raw_events_list = interest_rates + lendings + repayments
  #raw_events_list = RawEventsListCache().get_events()
  return raw_events_list

@Logging_config.execution_time_tracking
def fetch_interest_rates()->anvil.tables.SearchIterator:
  loan = app_tables.loans.search()[0]
  #interest_rates = [item.__dict__['_spec']['itemCache'] for item in app_tables.interest_rates.search(loan=loan)]
  interest_rates = app_tables.interest_rates.search(loan=loan)
  return interest_rates
#print(fetch_interest_rates())

@Logging_config.execution_time_tracking
def dict_fetched_interest_rates()->List[dict]:
  result = [dict(item) for item in fetch_interest_rates()]
  return result
#print(dict_fetched_interest_rates())


@Logging_config.execution_time_tracking
def dict_interest_rates():
  loan = app_tables.loans.search()[0]
  result = [{**dict(item), "event_type":"Interest rate", "loan_id":item['loan']['loan_id']} for item in app_tables.interest_rates.search(loan=loan)]
  return result
#print(dict_interest_rates())

@Logging_config.execution_time_tracking
def fetch_loan_events1()->List[dict]:
  '''
  Fetch loan events from the database.
  - Interest rates
  - Lendings
  - Repayments\n
  Returns a list of dictionaries with the combined event data.
  '''
  loan = app_tables.loans.search()[0]
  interest_rates = [{**dict(item), "event_type":"Interest rate", "loan_id":item['loan']['loan_id']} for item in
                    app_tables.interest_rates.search(loan=loan)]
  lendings = [{**dict(item), "event_type": "Lending", "loan_id":item['loan']['loan_id']} for item in 
              app_tables.principal_lendings.search(loan=loan)]
  repayments = [{**dict(item), "event_type": "Repayment", "loan_id":item['loan']['loan_id']} for item in 
                app_tables.repayments.search(loan=loan)]
  raw_events_list = interest_rates + lendings + repayments
  #raw_events_list = RawEventsListCache().get_events()
  return raw_events_list
#fetch_loan_events1()

def events_dataclass_listing()->List[Event]:
  '''
  Parses multiple events of different types to Event dataclass instances.
  '''
  raw_events_list: List[dict] = fetch_loan_events()
  loan_mapping: Dict[str, Loan] = loans_mapping()
  events_list = []
  for event in raw_events_list:
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

def sort_events_list()->List[Event]:
  events_list = events_dataclass_listing()
  events_list_sorted: List[Event] = sorted(events_list, key=lambda e: (e.event_start_date, e.event_id))
  return events_list_sorted

@anvil.server.callable
def extract_sorted_events_properties() -> List[Dict[str, str]]:
    """
    Extracts properties from each event and returns a list of dictionaries.
    Each dictionary contains the specified parameters for an event.
    """
  
    events_list = sort_events_list()  # Get the list of Event instances
    event_properties_list = []

    for event in events_list:
        event_dict = {
            "loan": event.loan.loan_id,
            "event_fact_date": str(event.event_fact_date),
            "event_start_date": str(event.event_start_date),
            "event_id": str(event.event_id),
            "event_type": event.event_type if hasattr(event, 'event_type') else None, 
            "principal_lending_currency.currency_amount": str(event.principal_lending_currency.currency_amount) if event.principal_lending_currency else None,
            "principal_lending_currency.ticker": event.principal_lending_currency.ticker if event.principal_lending_currency else None,
            "principal_lending_currency.currency_to_loan_rate": str(event.principal_lending_currency.currency_to_loan_rate) if event.principal_lending_currency else None,
            "principal_lending": str(event.principal_lending) if event.principal_lending is not None else None,
            "interest_rate": f"{event.interest_rate:.2f}" if event.interest_rate is not None else None,
            "interest_rate_base": str(event.interest_rate_base) if event.interest_rate_base is not None else None,
            "principal_repayment_currency.currency_amount": str(event.principal_repayment_currency.currency_amount) if event.principal_repayment_currency else None,
            "principal_repayment_currency.ticker": event.principal_repayment_currency.ticker if event.principal_repayment_currency else None,
            "principal_repayment_currency.currency_to_loan_rate": str(event.principal_repayment_currency.currency_to_loan_rate) if event.principal_repayment_currency else None,
            "principal_repayment": str(event.principal_repayment) if event.principal_repayment is not None else None,
            "interest_repayment_currency.currency_amount": str(event.interest_repayment_currency.currency_amount) if event.interest_repayment_currency else None,
            "interest_repayment_currency.ticker": event.interest_repayment_currency.ticker if event.interest_repayment_currency else None,
            "interest_repayment_currency.currency_to_loan_rate": str(event.interest_repayment_currency.currency_to_loan_rate) if event.interest_repayment_currency else None,
            "interest_repayment": str(event.interest_repayment) if event.interest_repayment is not None else None,
        }
        event_properties_list.append(event_dict)

    return event_properties_list
  
  
#********************************
# DEBUG: print sorted List[Event]
#print(type(sort_events_list()[0]))
#print(sort_events_list()[0])
def print_events_list()->None:
  print("-" * 180)
  print(f"{'Date':<12} {'Start event date':<12} {'Currency lending':>18} {'Currency':>10} {'Rate':>10} {'Principal lending':>18} {'Principal repayment':>18} {'Interest repayment':>18} {'Event IDs':>12}")
  print("-" * 180)
  events_list_sorted = sort_events_list()
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

#print_events_list()
#********************************

# ==============================
# 3. Aggregate Events by Date
# ==============================
def agregate_events_by_date() -> Dict[datetime, AggregatedEvent]:
  '''
  Sum existing values for each event_fact_date (ex: 2 repayment events in a day).
  Insert default values from AggregatedEvents class if event does not have a value (None)
  '''
  aggregated_events: Dict[datetime, AggregatedEvent] = defaultdict(lambda: AggregatedEvent(loan=loans_mapping()['0eb8f023-87a2-4a36-b045-d7892519a643'], 
                                                                                        event_fact_date = None,
                                                                                        event_start_date =None))
  events_list_sorted = sort_events_list()
  for event in events_list_sorted:
      date_key = event.event_start_date
      if aggregated_events[date_key].event_start_date is None:
          aggregated_events[date_key].event_start_date = event.event_start_date
      if aggregated_events[date_key].event_fact_date is None:
          aggregated_events[date_key].event_fact_date = event.event_fact_date
      # Convert repayment to loan currency and aggregate
      if event.principal_lending:
          aggregated_events[date_key].principal_lending +=event.principal_lending
      if event.principal_repayment:
          aggregated_events[date_key].principal_repayment +=event.principal_repayment
      if event.interest_repayment:
          aggregated_events[date_key].interest_repayment +=event.interest_repayment
      # Aggregate other fields (assumed to be in base currency)
      if event.capitalization:
        aggregated_events[date_key].capitalization += event.capitalization
      if event.interest_rate:
        aggregated_events[date_key].interest_rate = event.interest_rate
      if event.principal_balance_correction:
        aggregated_events[date_key].principal_balance_correction += event.principal_balance_correction
      if event.interest_balance_correction:
        aggregated_events[date_key].interest_balance_correction += event.interest_balance_correction
      aggregated_events[date_key].event_ids.append(event.event_id)
  return aggregated_events

# ==============================
# 4. Generate Dates
# ==============================
def generate_date_list(dates_generator_range_start: str, 
                      dates_generator_range_end: str, 
                      dates_generator_frequency: str) -> List[datetime]:
    """Generate a list of datetime objects at a given frequency."""
    return pd.date_range(start=dates_generator_range_start, 
                        end=dates_generator_range_end, 
                        freq=dates_generator_frequency, 
                        inclusive='left').date.tolist()

def add_generated_dates_to_aggregated_events_list()->List[AggregatedEvent]:
  '''
  Creates sorted list of AggregatedEvents with generated dates.
  '''
  # Date range for the entire timeline
  aggregated_events = agregate_events_by_date()
  dates_generator_range_start = min(aggregated_events.keys())
  # use time delta to add last month to the statistics
  dates_generator_range_end = max(aggregated_events.keys()) + timedelta(days=31)
  loan: Loan = loans_mapping()['0eb8f023-87a2-4a36-b045-d7892519a643']
  # Capitalization: generate capitalization dates (Quarterly start 'QS' frequency)
  if loan.capitalization == True:
    capitalization_generated_dates = generate_date_list(
      dates_generator_range_start=dates_generator_range_start,  #datetime .strftime("%Y-%m-%d"), 
      dates_generator_range_end=dates_generator_range_end,      #datetime .strftime("%Y-%m-%d"), 
      dates_generator_frequency="QS")
    # Add capitalization dates to aggregated_events
    for capitalization_generated_date in capitalization_generated_dates:
      aggregated_events[capitalization_generated_date] = AggregatedEvent(loan=loans_mapping()['0eb8f023-87a2-4a36-b045-d7892519a643'], 
                                                            event_start_date=capitalization_generated_date,
                                                            event_fact_date=capitalization_generated_date, 
                                                            capitalization=Decimal('0.0'))
  # Interest: year days count (leap year -> st year -> leap year) changes 
  if loan.interest_rate_base == 'calendar':
    interest_year_base_generated_dates = generate_date_list(
      dates_generator_range_start=dates_generator_range_start,  #datetime .strftime("%Y-%m-%d"), 
      dates_generator_range_end=dates_generator_range_end,      #datetime .strftime("%Y-%m-%d"), 
      dates_generator_frequency="YS")
    # Add missing dates to aggregated_events
    for generated_year_switch_date in interest_year_base_generated_dates:
        if generated_year_switch_date not in aggregated_events:
            aggregated_events[generated_year_switch_date] = AggregatedEvent(loan=loans_mapping()['0eb8f023-87a2-4a36-b045-d7892519a643'], 
                                                                  event_fact_date=generated_year_switch_date, 
                                                                  event_start_date=generated_year_switch_date)

  # Generate missing dates (Monthly start 'MS' frequency)
  generated_reporting_dates = generate_date_list(
    dates_generator_range_start=dates_generator_range_start,  #datetime .strftime("%Y-%m-%d"), 
    dates_generator_range_end=dates_generator_range_end,      #datetime .strftime("%Y-%m-%d"), 
    dates_generator_frequency="MS")
  # Add missing report dates to aggregated_events
  for generated_report_date in generated_reporting_dates:
      if generated_report_date not in aggregated_events:
          aggregated_events[generated_report_date] = AggregatedEvent(loan=loans_mapping()['0eb8f023-87a2-4a36-b045-d7892519a643'], 
                                                                event_fact_date=generated_report_date, 
                                                                event_start_date=generated_report_date)
# Convert to sorted list
  aggregated_events_added_dates = aggregated_events
  events_list_date_aggregated_sorted = sorted(aggregated_events_added_dates.values(), key=lambda e: e.event_start_date)
  return events_list_date_aggregated_sorted, capitalization_generated_dates

#******************************************
# DEBUG: print sorted List[AggregatedEvent]
def print_aggregated_events_list():    
  print("-" * 140)
  print(f"{'Date':<12} {'Lending':>8} {'Pr_rep':>10}{'Int_rep':>10}{'Event IDs':>30}")  # Adjusted width for Event IDs
  print("-" * 140)
  events_list_date_aggregated_sorted, capitalization_generated_dates = add_generated_dates_to_aggregated_events_list()
  for event in events_list_date_aggregated_sorted:
      event_start_date = str(event.event_start_date)
      print(f"{event_start_date:<12}" 
            f"{event.principal_lending:>8}" 
            f"{event.principal_repayment:>10}"
            f"{event.interest_repayment:>10}"
            f"{str(event.event_ids):<30}")  # Adjusted width for Event IDs
  print("-" * 140)
  
#print_aggregated_events_list()
#*******************************************

# ==============================
# 5. Calculate Principal Balances, Days Count & Interest
# ==============================
  
def loan_parameters_calculations():
  loan: Loan = loans_mapping()['0eb8f023-87a2-4a36-b045-d7892519a643']
  events_list_date_aggregated_sorted, capitalization_generated_dates = add_generated_dates_to_aggregated_events_list()
  principal_balance = Decimal('0.0')
  interest_balance = Decimal('0.0')
  current_interest_rate = Decimal('0.0')  # Default interest rate
  
  for i, event in enumerate(events_list_date_aggregated_sorted):
      # Update current_interest_rate if there's a rate change on this event_fact_date
      if event.interest_rate > 0:
          current_interest_rate = Decimal(str(event.interest_rate))
      event.interest_rate = current_interest_rate

      if loan.capitalization == True:
        if event.event_start_date in capitalization_generated_dates:
            event.capitalization = interest_balance
            #print(f"Capitalization on {event.event_start_date} amount: {interest_balance}")
      # Update principal balance
      principal_balance += (
          Decimal(event.principal_lending) +
          Decimal(event.capitalization) -
          Decimal(event.principal_repayment) +
          Decimal(event.principal_balance_correction)
      )
      event.principal_balance = principal_balance  
      #print(principal_balance)
      
      # Calculate days_count (difference between next event event_fact_date and current event_fact_date)
      if i < len(events_list_date_aggregated_sorted) - 1:
          next_event = events_list_date_aggregated_sorted[i + 1]
          event.days_count = (next_event.event_start_date - event.event_start_date).days
      else:
          event.days_count = 0  # Last event has no next event_fact_date

      if i < len(events_list_date_aggregated_sorted) - 1 and event.days_count >1:
          event.event_end_date = (event.event_start_date+timedelta(event.days_count-1))
      else:
          event.event_end_date = event.event_start_date

      # Calculate interest accrued
      if loan.interest_rate_base == 'calendar': 
        interest_rate_base = 366 if pd.Timestamp(event.event_start_date).is_leap_year else 365
        event.interest_accrued = (current_interest_rate / interest_rate_base) * Decimal(event.days_count) * event.principal_balance
      else:
        interest_rate_base = loan.interest_rate_base
        event.interest_accrued = (current_interest_rate / interest_rate_base) * Decimal(event.days_count) * event.principal_balance
      event.interest_rate_base = interest_rate_base
      # Update interest balance
      interest_balance += (
          Decimal(event.interest_accrued) -
          Decimal(event.capitalization) -
          Decimal(event.interest_repayment)+
          Decimal(event.interest_balance_correction)
      )
      event.interest_balance = interest_balance
  calculated_loan = events_list_date_aggregated_sorted
  return calculated_loan


# ***************************************
# DEBUG  print loan calculations results
def print_calculated_loan():
  print("-" * 180)
  print(
    f"{'Event'        :<12}"\
    f"{'Start'        :>12}" \
    f"{'Days'         :>8}" \
    f"{'End'          :>12}" \
    f"{'Lending'      :>12}" \
    f"{'Cap'          :>12}" \
    f"{'Pr_rep'       :>12}" \
    f"{'Pr_balance'   :>14}" \
    f"{'Int_rate'     :>12}" \
    f"{'Int_base'     :>12}" \
    f"{'Int_accrued'  :>14}" \
    f"{'Int_rep'      :>12}" \
    f"{'Int_balance'  :>14}")
  print("-" * 180)
  calculated_loan = loan_parameters_calculations()
  for event in calculated_loan:
      event_fact_date = str(event.event_fact_date)
      event_start_date = str(event.event_start_date)
      event_end_date = str(event.event_end_date)
      print(f"{event_fact_date:<12}" 
          f"{event_start_date:>12}" 
            f"{event.days_count:>8}" 
            f"{event_end_date:>12}"  # Right-aligned for consistency
            f"{event.principal_lending:>12.2f}" 
            f"{event.capitalization:>12.2f}"
            f"{event.principal_repayment:>12.2f}" 
            f"{event.principal_balance:>14.2f}" 
            f"{event.interest_rate:>12.2f}"
            f"{event.interest_rate_base:>12.2f}"
            f"{float(event.interest_accrued):>14.2f}" 
            f"{event.interest_repayment:>12.2f}" 
            f"{float(event.interest_balance):>14.2f}"
            )
  print("-" * 180)
#print_calculated_loan()
#***************************************************************************
@anvil.server.callable
def extract_calculated_loan_properties() -> List[Dict[str, str]]:
    """
    Extracts properties from each calculated loan event and returns a list of dictionaries.
    Each dictionary contains the specified parameters for a calculated loan event.
    """
    calculated_loan = loan_parameters_calculations()  # Get the list of calculated loan events
    loan_properties_list = []

    for event in calculated_loan:
        loan_dict = {
            "Event": str(event.event_fact_date),
            "Start": str(event.event_start_date),
            "Days": event.days_count,
            "End": str(event.event_end_date),
            "Lending": str(event.principal_lending) if event.principal_lending is not None else None,
            "Cap": str(event.capitalization) if event.capitalization is not None else None,
            "Pr_rep": str(event.principal_repayment) if event.principal_repayment is not None else None,
            "Pr_balance": str(event.principal_balance) if event.principal_balance is not None else None,
            "Int_rate": f"{event.interest_rate:.2f}" if event.interest_rate is not None else None,
            "Int_base": str(event.interest_rate_base) if event.interest_rate_base is not None else None,
            "Int_accrued": str(event.interest_accrued) if event.interest_accrued is not None else None,
            "Int_rep": str(event.interest_repayment) if event.interest_repayment is not None else None,
            "Int_balance": str(event.interest_balance) if event.interest_balance is not None else None,
        }
        loan_properties_list.append(loan_dict)
    return loan_properties_list
  
#print(extract_calculated_loan_properties())