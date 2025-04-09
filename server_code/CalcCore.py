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
# Additional import
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Union, Literal
from collections import defaultdict
from decimal import Decimal, getcontext, localcontext
import pandas as pd


@anvil.server.callable
def calc_fetch_loan_events():
  interest_rates = [{**dict(item), "event_type":"Interest rate", "loan_id":item['loan']['loan_id']} for item in
                   app_tables.interest_rates.search(loan=app_tables.loans.search()[0])]
  lendings = [{**dict(item), "event_type": "Lending", "loan_id":item['loan']['loan_id']} for item in 
              app_tables.principal_lendings.search(loan=app_tables.loans.search()[0])]
  repayments = [{**dict(item), "event_type": "Repayment", "loan_id":item['loan']['loan_id']} for item in app_tables.repayments.search(loan=app_tables.loans.search()[0])]

  events_list_raw = interest_rates + lendings + repayments
  print(events_list_raw)
  return events_list_raw

#@anvil.server.callable
def calc_fetch_loan_info():
  loans_list = [dict(app_tables.loans.search()[0])]
  print(loans_list)
  return loans_list


# Set global precision to 6 decimal places
getcontext().prec = 6
# ==============================
# 1. Define Data Classes
# ==============================
@dataclass
class Loan:
    loan_id: int
    base_currency: str
    interest_rate_base: Union[Literal[360, 365], Literal['calendar']] = 365
    lending_date_exclusive_counting: bool = False
    repayment_date_exclusive_counting: bool = True
    capitalization: bool = False

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
# 2. Sample input data (Loans, Events)
# ==============================

@anvil.server.callable
def loans_list():
  loans_list_raw = calc_fetch_loan_info()
  loans_list = [Loan(**loan) for loan in loans_list_raw]
  print(loans_list)

#loan_mapping = {loan.loan_id: loan for loan in loans_list}


