'''
- [ ] VIZ: events, currency, full table
- [ ] add event types: 0-lending, 1 - interest rate setting, 2 - interest repayment, 
- [ ] cleanup capitalization attribute
- [ ] prescision issues

- [?] move interest_rate_base calculation to event generator (if interest_rate_base is None -> define for added date (year switch))

- [x] add year days count base(360,365,366, calendar) 
- [x] starting and ending period dates
- [x] lending and repayment offset (inclusive counting)
'''

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Union, Literal
from datetime import datetime, timedelta
from collections import defaultdict
from decimal import Decimal, getcontext, localcontext
import pandas as pd


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

loans_list_raw = [
    {'loan_id':101, 
    'base_currency': 'USD',
    'interest_rate_base': 'calendar',
    'lending_date_exclusive_counting': False,
    'repayment_date_exclusive_counting': True,
    'capitalization': True
    }
]
loans_list = [Loan(**loan) for loan in loans_list_raw]
loan_mapping = {loan.loan_id: loan for loan in loans_list}

'''
TODO Use string or float for numeric values (inclding interest_rate, principal_lending_currency, repayment, capitalization, principal_balance_correction, interest_balance_correction)
- "interest_rate": 0.06 - > 0.059999999999999997779553950749686919152736663818359375
- "interest_rate": '0.06' -> 0.06
This lead to glitches in the balance calculations and printing (15.49+17.5 != 32.65):
2023-02-01        28     3366.00        0.00       3366.00         15.49        0.00         15.49
2023-03-01        31        0.00        0.00       3366.00         17.15        0.00         32.65
'''
events_list_raw = [
    {"event_id": 1, "event_fact_date": "2024-02-01", "principal_lending_currency": 300, "loan_id": 101},
    {"event_id": 2, "event_fact_date": "2024-01-03", "principal_lending_currency": 400, "loan_id": 101},
    {"event_id": 3, "event_fact_date": "2025-02-18", "principal_lending_currency": 140, "currency": "EUR", "loan_id": 101, "currency_to_loan_rate": 1.15},
    {"event_id": 4, "event_fact_date": "2024-01-03", "principal_lending_currency": 333, "currency": "EUR", "loan_id": 101, "currency_to_loan_rate": 1.2},
    {"event_id": 5, "event_fact_date": "2023-02-01", "principal_lending_currency": 3366, "loan_id": 101},
    {"event_id": 6, "event_fact_date": "2024-01-04", "principal_repayment_currency": 21302, "currency": "USD", "loan_id": 101},
    {"event_id": 7, "event_fact_date": "2023-02-01", "interest_rate": 0.06, "loan_id": 101},
    {"event_id": 8, "event_fact_date": "2023-07-22", "principal_lending_currency": 43200, "currency": "USD", "loan_id": 101},
    {"event_id": 9, "event_fact_date": "2024-03-14", "principal_repayment_currency": 10302, "currency": "USD", "loan_id": 101},
    {"event_id": 10, "event_fact_date": "2024-01-15", "interest_repayment_currency": 130, "currency": "EUR", "loan_id": 101, "currency_to_loan_rate": 1.1},
    {"event_id": 11, "event_fact_date": "2024-11-03", "interest_repayment_currency": 180, "currency": "USD", "loan_id": 101},
    {"event_id": 7, "event_fact_date": "2024-07-05", "interest_rate": 0.13, "loan_id": 101},
]

# Convert raw data into `Event` objects with Currency attributes and associated loans
events_list: List[Event] = []
for event in events_list_raw:
    loan = loan_mapping.get(event.get("loan_id"))
    if not loan:
        raise ValueError(f"Loan with ID {event.get('loan_id')} not found.")
    event_fact_date = datetime.strptime(event["event_fact_date"], "%Y-%m-%d")
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
        currency_ticker = event.get("currency", loan.base_currency)  # Event currency
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

    if "principal_repayment_currency" in event:
        repayment_date_exclusive_counting = loan.repayment_date_exclusive_counting
        currency_ticker = event.get("currency", loan.base_currency)  # Event currency
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

    if "interest_repayment_currency" in event:
        repayment_date_exclusive_counting = loan.repayment_date_exclusive_counting
        currency_ticker = event.get("currency", loan.base_currency)  # Event currency
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
# Sort events by event_fact_date and event_id
events_list_sorted: List[Event] = sorted(events_list, key=lambda e: (e.event_start_date, e.event_id))
print("-" * 180)
print(f"{'Date':<12} {'Start event date':<12} {'Currency lending':>18} {'Currency':>10} {'Rate':>10} {'Principal lending':>18} {'Principal repayment':>18} {'Interest repayment':>18} {'Event IDs':>12}")
print("-" * 180)
for event in events_list_sorted:
    event_fact_date = str(event.event_fact_date.date())  # Ensure event_fact_date is a string
    event_start_date = str(event.event_start_date.date()) 
    lending_amount = f"{event.principal_lending_currency.currency_amount:.2f}" if event.principal_lending_currency and event.principal_lending_currency.currency_amount is not None else ""
    lending_currency = event.principal_lending_currency.ticker if event.principal_lending_currency else ""
    currency_rate = f"{event.principal_lending_currency.currency_to_loan_rate:.4f}" if event.principal_lending_currency and event.principal_lending_currency.currency_to_loan_rate is not None else ""
    principal_lending = f"{event.principal_lending:.2f}" if event.principal_lending is not None else ""
    principal_repayment = f"{event.principal_repayment:.2f}" if event.principal_repayment is not None else ""
    interest_repayment = f"{event.interest_repayment:.2f}" if event.interest_repayment is not None else ""
    event_id = str(event.event_id) if event.event_id is not None else ""

    print(f"{event_fact_date:<12} {event_start_date:<12}{lending_amount:>18} {lending_currency:>10} {currency_rate:>10} {principal_lending:>18} {principal_repayment:>18} {interest_repayment:>18} {event_id:>12}")

print("-" * 180)


# ==============================
# 3. Aggregate Events by Date
# ==============================
aggregated_events: Dict[datetime, AggregatedEvent] = defaultdict(lambda: AggregatedEvent(loan=loan_mapping[101], 
                                                                                        event_fact_date = None,
                                                                                        event_start_date =None))
'''
Sum existing values for each event_fact_date.
Insert deafault values from AggregatedEvents class if event does not have a value (None)
'''
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
                        inclusive='left').to_list()

# Date range for the entire timeline
dates_generator_range_start = min(aggregated_events.keys())
dates_generator_range_end = max(aggregated_events.keys()) + timedelta(days=31)

# Capitalization: generate capitalization dates (Quarterly start 'QS' frequency)
if loan.capitalization == True:
  capitalization_generated_dates = generate_date_list(
    dates_generator_range_start=dates_generator_range_start,  #datetime .strftime("%Y-%m-%d"), 
    dates_generator_range_end=dates_generator_range_end,      #datetime .strftime("%Y-%m-%d"), 
    dates_generator_frequency="QS")
  # Add capitalization dates to aggregated_events
  for capitalization_generated_date in capitalization_generated_dates:
    aggregated_events[capitalization_generated_date] = AggregatedEvent(loan=loan_mapping[101], 
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
          aggregated_events[generated_year_switch_date] = AggregatedEvent(loan=loan_mapping[101], 
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
        aggregated_events[generated_report_date] = AggregatedEvent(loan=loan_mapping[101], 
                                                              event_fact_date=generated_report_date, 
                                                              event_start_date=generated_report_date)


# Convert to sorted list
events_list_date_aggregated_sorted = sorted(aggregated_events.values(), key=lambda e: e.event_start_date)

print("-" * 140)
print(f"{'Date':<12} {'Lending':>8} {'Pr_rep':>10}{'Int_rep':>10}{'Event IDs':>12}")
print("-" * 140)
for event in events_list_date_aggregated_sorted:
    event_start_date = str(event.event_start_date)
    print(f"{event_start_date:<12}" 
          f"{event.principal_lending:>8}" 
          f"{event.principal_repayment:>10}"
          f"{event.interest_repayment:>10}"
          f"{str(event.event_ids):>12}")
print("-" * 140)


# ==============================
# 5. Calculate Principal Balances, Days Count & Interest
# ==============================
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
          print(f"Capitalization on {event.event_start_date} amount: {interest_balance}")
    # Update principal balance
    principal_balance += (
        Decimal(event.principal_lending) +
        Decimal(event.capitalization) -
        Decimal(event.principal_repayment) +
        Decimal(event.principal_balance_correction)
    )
    event.principal_balance = principal_balance  
    
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
    
# ==============================
# 6. Print Results
# ==============================

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

for event in events_list_date_aggregated_sorted:
    event_fact_date = str(event.event_fact_date.date())
    event_start_date = str(event.event_start_date.date())
    event_end_date = str(event.event_end_date.date())
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



# ==============================
# 7. Analytical Function: Balance Report
# ==============================
def balance_report(data: List[AggregatedEvent], report_date: str) -> float:
    """Returns the principal balance on a given event_fact_date."""
    report_date = datetime.strptime(report_date, "%Y-%m-%d")

    if report_date < data[0].event_fact_date:
        return 0  # Before any recorded events

    previous_balance = 0
    for event in data:
        if event.event_start_date == report_date:
            return float(event.principal_balance)
        elif event.event_fact_date > report_date:
            return previous_balance  # Last known balance before the report_date
        previous_balance = float(event.principal_balance)

    return previous_balance  # Return last balance if report_date is in the future

# Test balance report
print("\nPrincipal balance Report:")
print(f"Principal balance on 2024-01-03: {balance_report(events_list_date_aggregated_sorted, '2024-01-03')}")
print(f"Principal balance on 2025-01-01: {balance_report(events_list_date_aggregated_sorted, '2025-01-01')}")
print(f"Principal balance on 2022-12-31: {balance_report(events_list_date_aggregated_sorted, '2022-12-31')}")



# ==============================
# 8. Plotting with Plotly
# ==============================

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Convert Aggregated Events to a DataFrame—
data = {
    'Date': [event.event_fact_date for event in events_list_date_aggregated_sorted],
    'Days Count': [event.days_count for event in events_list_date_aggregated_sorted],
    'Lending': [float(event.principal_lending) for event in events_list_date_aggregated_sorted],
    'Repayment': [float(event.principal_repayment) for event in events_list_date_aggregated_sorted],
    'Principal Balance': [float(event.principal_balance) for event in events_list_date_aggregated_sorted],
    'Interest Accrued': [float(event.interest_accrued) for event in events_list_date_aggregated_sorted],
    'Interest Balance': [float(event.interest_balance) for event in events_list_date_aggregated_sorted],
    'Event IDs': [event.event_ids for event in events_list_date_aggregated_sorted]
}

df = pd.DataFrame(data)

# Ensure the 'Date' column is of datetime type
df['Date'] = pd.to_datetime(df['Date'])

# Sort the DataFrame by Date
df = df.sort_values('Date')

# Plot Interest Accrued Balance Over Time
fig_interest = px.line(
    df,
    x='Date',
    y='Interest Balance',
    title='Interest Accrued Balance Over Time',
    labels={
        'Date': 'Date',
        'Interest Balance': 'Interest Balance (USD)'
    }
)

fig_interest.update_layout(
    xaxis_title='Date',
    yaxis_title='Interest Balance (USD)',
    template='plotly_white'
)

#fig_interest.show()

# Plot Principal Balance Over Time
# Add markers for Repayment dates
fig_principal = px.line(
    df,
    x='Date',
    y='Principal Balance',
    title='Principal Balance Over Time',
    labels={
        'Date': 'Date',
        'Principal Balance': 'Principal Balance (USD)'
    }
)

# Highlight repayment points
repayment_dates = df[df['Repayment'] > 0]['Date']
repayment_balances = df[df['Repayment'] > 0]['Principal Balance']

fig_principal.add_trace(
    go.Scatter(
        x=repayment_dates,
        y=repayment_balances,
        mode='markers',
        name='Repayment',
        marker=dict(color='red', size=10, symbol='triangle-up')
    )
)

fig_principal.update_layout(
    xaxis_title='Date',
    yaxis_title='Principal Balance (USD)',
    template='plotly_white'
)

#fig_principal.show()

"""fig_principal = px.line(
    df,
    x='Date',
    y='Principal Balance',
    title='Principal Balance Over Time',
    labels={
        'Date': 'Date',
        'Principal Balance': 'Principal Balance (USD)'
    }
)

fig_principal.update_layout(
    xaxis_title='Date',
    yaxis_title='Principal Balance (USD)',
    template='plotly_white'
)

fig_principal.show()"""

# Optional: Combined Chart with Dual Y-Axes
fig_combined = make_subplots(specs=[[{"secondary_y": True}]])

# Add Principal Balance trace
fig_combined.add_trace(
    go.Scatter(x=df['Date'], y=df['Principal Balance'], name='Principal Balance', line=dict(color='blue')),
    secondary_y=False,
)

# Add Interest Balance trace
fig_combined.add_trace(
    go.Scatter(x=df['Date'], y=df['Interest Balance'], name='Interest Balance', line=dict(color='red')),
    secondary_y=True,
)

# Add titles and labels
fig_combined.update_layout(
    title_text="Principal and Interest Balances Over Time",
    template='plotly_white'
)

fig_combined.update_xaxes(title_text="Date")
fig_combined.update_yaxes(title_text="Principal Balance (USD)", secondary_y=False)
fig_combined.update_yaxes(title_text="Interest Balance (USD)", secondary_y=True)

#fig_combined.show()
