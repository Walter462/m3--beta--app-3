from dataclasses import dataclass, field, asdict
from typing import Optional, List
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
    """Represents a monetary value with its currency.
    - [ ] add currency API to fetch conversion rates at user input
    - [ ] add currency_to_loan_rate (transaction currency != loan_currency)
    - [ ] add ticker consistency check (USD+EUR->error (-,/,*< sum, == etc.))
    - [x] add support for currency conversion
    """
    currency_amount: Decimal
    ticker: str
    currency_to_loan_rate: Decimal = Decimal('1.0')  # Conversion rate to loan currency
    def converted_amount(self) -> Decimal:
        """Converts the currency amount to the loan's base currency."""
        return self.currency_amount * self.currency_to_loan_rate



@dataclass
class Event:
    """Represents an individual financial event."""
    loan_id: Loan
    event_id: int
    date: datetime
    principal_lending: Currency = None
    capitalization: Decimal = Decimal('0.0')  # Assumed to be in base currency
    repayment: Currency = None
    principal_balance_correction: Decimal = Decimal('0.0')  # Assumed to be in base currency
    interest_balance_correction: Decimal = Decimal('0.0')  # Assumed to be in base currency

@dataclass
class AggregatedEvent:
    """Represents aggregated events grouped by date."""
    date: datetime
    principal_lending: Decimal = Decimal('0.0') 
    capitalization: Decimal = Decimal('0.0')
    repayment: Decimal = Decimal('0.0')
    principal_balance_correction: Decimal = Decimal('0.0')  # Assumed to be in base currency
    interest_balance_correction: Decimal = Decimal('0.0')  # Assumed to be in base currency
    event_ids: List[int] = field(default_factory=list)
    # Additionaly calculated filelds
    principal_balance: Decimal = Decimal('0.0')
    days_count: int = 0
    interest_accrued: Decimal  = Decimal('0.0')
    interest_balance: Decimal  = Decimal ('0.0')
    
# ==============================
# 2. Sample input data (Loans, Events)
# ==============================

loans_list_raw = [
    {'loan_id':101, 'base_currency': 'USD'},
    {'loan_id':102, 'base_currency': 'EUR'}
]
loans_list = [Loan(**loan) for loan in loans_list_raw]
loan_mapping = {loan.loan_id: loan for loan in loans_list}

events_list_raw = [
    {"event_id": 1, "date": "2024-02-01", "principal_lending": 300, "currency": "USD", "loan_id": 101},
    {"event_id": 2, "date": "2024-01-03", "principal_lending": 400, "currency": "USD", "loan_id": 101},
    {"event_id": 3, "date": "2025-02-18", "principal_lending": 120, "currency": "EUR", "loan_id": 102},
    {"event_id": 4, "date": "2024-01-03", "principal_lending": 333, "currency": "USD", "loan_id": 101, "currency_to_loan_rate": 1.01},
    {"event_id": 5, "date": "2023-02-01", "principal_lending": 3366, "currency": "USD", "loan_id": 101},
    {"event_id": 6, "date": "2024-01-04", "repayment": 21302, "currency": "EUR", "loan_id": 102},
    {"event_id": 7, "date": "2023-02-01", "interest_rate": 0.06, "loan_id": 101},
    {"event_id": 8, "date": "2023-07-22", "principal_lending": 43200, "currency": "USD", "loan_id": 101}
]

# Convert raw data into `Event` objects with Currency attributes and associated loans
events_list = []
for event in events_list_raw:
    principal_lending = None
    repayment = None
    loan = loan_mapping.get(event.get("loan_id"))
    if not loan:
        raise ValueError(f"Loan with ID {event.get('loan_id')} not found.")

    if "principal_lending" in event and "currency" in event:
        currency_ticker = event.get("currency", loan.base_currency)
        currency_rate = Decimal('1.0')
        # If transaction currency differs from loan's base currency, adjust the rate
        if currency_ticker != loan.base_currency:
            # Example conversion: EUR to USD (assuming loan base is USD)
            currency_rate = event.get("currency_to_loan_rate")
        principal_lending = Currency(
            currency_amount=Decimal(event["principal_lending"]),
            ticker=currency_ticker,
            currency_to_loan_rate=currency_rate
        )
    
    if "repayment" in event and "currency" in event:
        currency_ticker = event.get("currency", loan.base_currency)
        currency_rate = Decimal('1.0')
        if currency_ticker != loan.base_currency:
            currency_rate = event.get("currency_to_loan_rate")
        repayment = Currency(
            currency_amount=Decimal(event["repayment"]),
            ticker=currency_ticker,
            currency_to_loan_rate=currency_rate
        )
    
    # Create the Event instance
    events_list.append(
        Event(
            event_id=event["event_id"],
            date=datetime.strptime(event["date"], "%Y-%m-%d"),
            loan_id=loan,
            principal_lending=principal_lending,
            capitalization=event.get("capitalization", Decimal('0.0')),
            repayment=repayment,
            principal_balance_correction=event.get("principal_balance_correction",  Decimal('0.0')),
            interest_balance_correction=event.get("interest_balance_correction", Decimal('0.0')))
        )

# Sort events by date and event_id
events_list_sorted = sorted(events_list, key=lambda e: (e.date, e.event_id))

# ==============================
# 3. Aggregate Events by Date
# ==============================
aggregated_events = defaultdict(lambda: AggregatedEvent(date=None))

for event in events_list_sorted:
    date_key = event.date
    if aggregated_events[date_key].date is None:
        aggregated_events[date_key].date = event.date
    
    # Convert principal_lending to loan currency and aggregate
    if event.principal_lending:
        aggregated_events[date_key].principal_lending += event.principal_lending.converted_amount()
    
    # Convert repayment to loan currency and aggregate
    if event.repayment:
        aggregated_events[date_key].repayment += event.repayment.converted_amount()
    
    # Aggregate other fields (assumed to be in base currency)
    aggregated_events[date_key].capitalization += event.capitalization
    aggregated_events[date_key].principal_balance_correction += event.principal_balance_correction
    aggregated_events[date_key].interest_balance_correction += event.interest_balance_correction
    aggregated_events[date_key].event_ids.append(event.event_id)

# ==============================
# 4. Generate Dates
# ==============================
def generate_date_list(start_date: str, end_date: str, frequency: str) -> List[datetime]:
    """Generate a list of datetime objects at a given frequency."""
    return pd.date_range(start=start_date, end=end_date, freq=frequency, inclusive='left').to_list()

# Generate missing dates (Monthly start 'MS' frequency)
generated_dates = generate_date_list(
  start_date=min(*aggregated_events), 
  end_date=max(*aggregated_events)+timedelta(days=31), 
  frequency="MS")


# Add missing dates to aggregated_events
for date in generated_dates:
    if date not in aggregated_events:
        aggregated_events[date] = AggregatedEvent(date=date)

# Convert to sorted list
events_list_date_aggregated_sorted = sorted(aggregated_events.values(), key=lambda e: e.date)

print("-" * 120)
print(f"{'Date':<12} {'Lending':>8} {'Repayment':>10}{'Event IDs'}")
print("-" * 120)
for event in events_list_date_aggregated_sorted:
    print(f"{event.date.date()} {event.principal_lending:>8} {event.repayment:>10} "
          f" {event.event_ids}")
print("-" * 120)

# ==============================
# 5. Calculate Principal Balances, Days Count & Interest
# ==============================
principal_balance = Decimal('0.0')
interest_balance = Decimal('0.0')
current_interest_rate = Decimal('0.0')  # Default interest rate

for i, event in enumerate(events_list_date_aggregated_sorted):
    # Check if there was an interest rate update on this date
    for raw_event in events_list_raw:
        if datetime.strptime(raw_event["date"], "%Y-%m-%d") == event.date and "interest_rate" in raw_event:
            current_interest_rate = Decimal(str(raw_event["interest_rate"]))
    
    # Update principal balance
    principal_balance += (
        event.principal_lending +
        Decimal(event.capitalization) -
        event.repayment +
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
    interest_balance += event.interest_accrued
    event.interest_balance = interest_balance

print("-" * 120)
print(f"{'Date':<12} {'Lending (USD)':>15} {'Repayment (USD)':>18} {'Capitalization':>15} {'Event IDs'}")
print("-" * 120)
for event in events_list_date_aggregated_sorted:
    print(f"{event.date.date()} {event.principal_lending:>15.2f} {event.repayment:>18.2f} {event.capitalization:>15.2f} {event.event_ids}")
print("-" * 120)

# ==============================
# 6. Print Results
# ==============================
# Print results including interest calculations
print("-" * 120)
print(f"{'Date':<12} {'Days Count':>12} {'Lending':>8} {'Repayment':>10} {'Balance':>10} {'Interest Accrued':>18} {'Interest Balance':>18} {'Event IDs'}")
print("-" * 120)
for event in events_list_date_aggregated_sorted:
    print(f"{event.date.date()} {event.days_count:>12} {event.principal_lending:>8} {event.repayment:>10} "
          f"{event.principal_balance:>10} {event.interest_accrued:>18.2f} {event.interest_balance:>18.2f} {event.event_ids}")
print("-" * 120)


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
            return event.principal_balance
        elif event.date > report_date:
            return previous_balance  # Last known balance before the report_date
        previous_balance = event.principal_balance

    return previous_balance  # Return last balance if report_date is in the future

# Test balance report
print("\nBalance Report:")
print(f"Balance on 2024-01-03: {balance_report(events_list_date_aggregated_sorted, '2024-01-03')}")
print(f"Balance on 2025-01-01: {balance_report(events_list_date_aggregated_sorted, '2025-01-01')}")
print(f"Balance on 2022-12-31: {balance_report(events_list_date_aggregated_sorted, '2022-12-31')}")