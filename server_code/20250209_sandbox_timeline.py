from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict
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
    date: Optional[datetime] = None
    event_id: Optional[int] = None
    principal_lending_currency: Optional[Currency] = None
    principal_lending: Optional[Decimal] = None
    capitalization: Decimal = None
    interest_rate: Optional[Decimal] = None

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
    date: datetime
    days_count: int = 0
    event_ids: List[int] = field(default_factory=list)
    principal_lending_currency: Currency = field(default_factory=lambda: Currency(currency_amount=Decimal('0.0'), ticker=None, currency_to_loan_rate=None))
    principal_lending: Decimal = Decimal('0.0')
    capitalization: Decimal = Decimal('0.0')
    interest_rate: Decimal = Decimal('0.0')

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
    {'loan_id':101, 'base_currency': 'USD'}
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
    {"event_id": 1, "date": "2024-02-01", "principal_lending_currency": 300, "loan_id": 101},
    {"event_id": 2, "date": "2024-01-03", "principal_lending_currency": 400, "loan_id": 101},
    {"event_id": 3, "date": "2025-02-18", "principal_lending_currency": 140, "currency": "EUR", "loan_id": 101, "currency_to_loan_rate": 1.15},
    {"event_id": 4, "date": "2024-01-03", "principal_lending_currency": 333, "currency": "EUR", "loan_id": 101, "currency_to_loan_rate": 1.2},
    {"event_id": 5, "date": "2023-02-01", "principal_lending_currency": 3366, "loan_id": 101},
    {"event_id": 6, "date": "2024-01-04", "principal_repayment_currency": 21302, "currency": "USD", "loan_id": 101},
    {"event_id": 7, "date": "2023-02-01", "interest_rate": 0.06, "loan_id": 101},
    {"event_id": 8, "date": "2023-07-22", "principal_lending_currency": 43200, "currency": "USD", "loan_id": 101},
    {"event_id": 9, "date": "2024-03-14", "principal_repayment_currency": 10302, "currency": "USD", "loan_id": 101},
    {"event_id": 10, "date": "2024-03-15", "interest_repayment_currency": 1302, "currency": "EUR", "loan_id": 101, "currency_to_loan_rate": 1.1},
    {"event_id": 11, "date": "2024-03-17", "interest_repayment_currency": 200, "currency": "USD", "loan_id": 101},
]

# Convert raw data into `Event` objects with Currency attributes and associated loans
events_list: List[Event] = []
for event in events_list_raw:
    loan = loan_mapping.get(event.get("loan_id"))
    if not loan:
        raise ValueError(f"Loan with ID {event.get('loan_id')} not found.")
    principal_lending_currency = None
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

    if "principal_repayment_currency" in event:
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

    if "interest_repayment_currency" in event:
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
            date=datetime.strptime(event["date"], "%Y-%m-%d"),
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
print(*events_list, sep="\n")
# Sort events by date and event_id
events_list_sorted: List[Event] = sorted(events_list, key=lambda e: (e.date, e.event_id))

print("-" * 140)
print(f"{'Date':<12} {'Currency lending':>18} {'Currency':>10} {'Rate':>10} {'Principal lending':>18} {'Principal repayment':>18} {'Interest repayment':>18} {'Event IDs':>12}")
print("-" * 140)
for event in events_list_sorted:
    date = str(event.date.date())  # Ensure date is a string
    lending_amount = f"{event.principal_lending_currency.currency_amount:.2f}" if event.principal_lending_currency and event.principal_lending_currency.currency_amount is not None else ""
    lending_currency = event.principal_lending_currency.ticker if event.principal_lending_currency else ""
    currency_rate = f"{event.principal_lending_currency.currency_to_loan_rate:.4f}" if event.principal_lending_currency and event.principal_lending_currency.currency_to_loan_rate is not None else ""
    principal_lending = f"{event.principal_lending:.2f}" if event.principal_lending is not None else ""
    principal_repayment = f"{event.principal_repayment:.2f}" if event.principal_repayment is not None else ""
    interest_repayment = f"{event.interest_repayment:.2f}" if event.interest_repayment is not None else ""
    event_id = str(event.event_id) if event.event_id is not None else ""

    print(f"{date:<12} {lending_amount:>18} {lending_currency:>10} {currency_rate:>10} {principal_lending:>18} {principal_repayment:>18} {interest_repayment:>18} {event_id:>12}")

print("-" * 140)


# ==============================
# 3. Aggregate Events by Date
# ==============================
aggregated_events: Dict[datetime, AggregatedEvent] = defaultdict(lambda: AggregatedEvent(loan=loan_mapping[101], date=None))
'''
Sum existing values for each date.
Insert deafault values from AggregatedEvents class if event does not have a value (None)
'''
for event in events_list_sorted:
    date_key = event.date
    if aggregated_events[date_key].date is None:
        aggregated_events[date_key].date = event.date
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
def generate_date_list(start_date: str, end_date: str, frequency: str) -> List[datetime]:
    """Generate a list of datetime objects at a given frequency."""
    return pd.date_range(start=start_date, end=end_date, freq=frequency, inclusive='left').to_list()

# Generate missing dates (Monthly start 'MS' frequency)
start_date = min(aggregated_events.keys())
end_date = max(aggregated_events.keys()) + timedelta(days=31)
generated_dates = generate_date_list(
  start_date=start_date.strftime("%Y-%m-%d"), 
  end_date=end_date.strftime("%Y-%m-%d"), 
  frequency="MS")

# Add missing dates to aggregated_events
for date in generated_dates:
    if date not in aggregated_events:
        aggregated_events[date] = AggregatedEvent(loan=loan_mapping[101], date=date)

# Convert to sorted list
events_list_date_aggregated_sorted = sorted(aggregated_events.values(), key=lambda e: e.date)


print("-" * 140)
print(f"{'Date':<12} {'Lending':>8} {'Pr_rep':>10}{'Int_rep':>10}{'Event IDs':>12}")
print("-" * 140)
for event in events_list_date_aggregated_sorted:
    date = str(event.date.date())
    print(f"{date:<12}" 
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
    # Update current_interest_rate if there's a rate change on this date
    if event.interest_rate > 0:
        current_interest_rate = Decimal(str(event.interest_rate))
    # Update principal balance
    principal_balance += (
        Decimal(event.principal_lending) +
        Decimal(event.capitalization) -
        Decimal(event.principal_repayment) +
        Decimal(event.principal_balance_correction)
    )
    event.principal_balance = principal_balance  
    
    # Calculate days_count (difference between next event date and current date)
    if i < len(events_list_date_aggregated_sorted) - 1:
        next_event = events_list_date_aggregated_sorted[i + 1]
        event.days_count = (next_event.date - event.date).days
    else:
        event.days_count = 0  # Last event has no next date
    
    # Calculate interest accrued
    event.interest_accrued = (current_interest_rate / Decimal('365')) * Decimal(event.days_count) * event.principal_balance
    
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

print("-" * 140)
print(f"\
{'Date'           :<12}" \
f"{'Days'         :>8}" \
f"{'Lending'      :>12}" \
f"{'Pr_rep'       :>12}" \
f"{'Pr_balance'   :>14}" \
f"{'Int_accrued'  :>14}" \
f"{'Int_rep'      :>12}" \
f"{'Int_balance'  :>14}")
print("-" * 140)

for event in events_list_date_aggregated_sorted:
    date = str(event.date.date())
    print(f"{date:<12}" 
          f"{event.days_count:>8}" 
          f"{event.principal_lending:>12.2f}" 
          f"{event.principal_repayment:>12.2f}" 
          f"{event.principal_balance:>14.2f}" 
          f"{float(event.interest_accrued):>14.2f}" 
          f"{event.interest_repayment:>12.2f}" 
          f"{float(event.interest_balance):>14.2f}"
          )
print("-" * 140)



# ==============================
# 7. Analytical Function: Balance Report
# ==============================
def balance_report(data: List[AggregatedEvent], report_date: str) -> float:
    """Returns the principal balance on a given date."""
    report_date = datetime.strptime(report_date, "%Y-%m-%d")

    if report_date < data[0].date:
        return 0  # Before any recorded events

    previous_balance = 0
    for event in data:
        if event.date == report_date:
            return float(event.principal_balance)
        elif event.date > report_date:
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
    'Date': [event.date for event in events_list_date_aggregated_sorted],
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
