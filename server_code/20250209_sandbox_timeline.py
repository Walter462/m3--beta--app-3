from dataclasses import dataclass, field, asdict
from typing import Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

# ==============================
# 1. Define Data Classes
# ==============================
@dataclass
class Event:
    """Represents an individual financial event."""
    event_id: int
    date: datetime
    principal_lending: float = 0.0
    currency: Optional[str] = None
    capitalization: float = 0.0
    repayment: float = 0.0
    principal_balance_correction: float = 0.0
    principal_balance: float = 0.0

@dataclass
class AggregatedEvent:
    """Represents aggregated events grouped by date."""
    date: datetime
    days_count: int = 0
    principal_lending: float = 0.0
    currency: Optional[str] = None
    capitalization: float = 0.0
    repayment: float = 0.0
    principal_balance_correction: float = 0.0
    principal_balance: float = 0.0
    interest_accrued: float = 0.0
    interest_balance: float = 0.0
    event_ids: List[int] = field(default_factory=list)
    
# ==============================
# 2. Sample Events
# ==============================
events_list_raw = [
    {"event_id": 1, "date": "2024-02-01", "principal_lending": 300, "currency": "USD"},
    {"event_id": 2, "date": "2024-01-03", "principal_lending": 400, "currency": "USD"},
    {"event_id": 3, "date": "2025-02-01", "principal_lending": 120, "currency": "USD"},
    {"event_id": 4, "date": "2024-01-03", "principal_lending": 333, "currency": "USD"},
    {"event_id": 5, "date": "2023-02-01", "principal_lending": 3366, "currency": "USD"},
    {"event_id": 6, "date": "2024-01-04", "repayment": 21302, "currency": "USD"},
    {"event_id": 7, "date": "2023-02-01", "interest_rate": 0.06},
    {"event_id": 8, "date": "2023-07-22", "principal_lending": 43200, "currency": "USD"}
]

# Convert raw data into `Event` objects
events_list = [
    Event(
        event_id=event["event_id"],
        date=datetime.strptime(event["date"], "%Y-%m-%d"),
        principal_lending=event.get("principal_lending", 0),
        repayment=event.get("repayment", 0),
        currency=event.get("currency", None),
    )
    for event in events_list_raw
]

# Sort events by date and event_id
events_list_sorted = sorted(events_list, key=lambda e: (e.date, e.event_id))

# ==============================
# 3. Aggregate Events by Date
# ==============================
aggregated_events = defaultdict(lambda: AggregatedEvent(date=None, currency=None))

for event in events_list:
    date_key = event.date
    if aggregated_events[date_key].date is None:
        aggregated_events[date_key] = AggregatedEvent(date=event.date, currency=event.currency)
    
    aggregated_events[date_key].principal_lending += event.principal_lending
    aggregated_events[date_key].repayment += event.repayment
    aggregated_events[date_key].event_ids.append(event.event_id)

# ==============================
# 4. Generate Missing Dates
# ==============================
def generate_date_list(start_date: str, end_date: str, frequency: str) -> List[datetime]:
    """Generate a list of datetime objects at a given frequency."""
    return pd.date_range(start=start_date, end=end_date, freq=frequency, inclusive='left').to_list()

# Generate missing dates (Monthly start 'MS' frequency)
generated_dates = generate_date_list(start_date="2023-01-03", end_date="2025-02-05", frequency="MS")

# Add missing dates to aggregated_events
for date in generated_dates:
    if date not in aggregated_events:
        aggregated_events[date] = AggregatedEvent(date=date)

# Convert to sorted list
events_list_date_aggregated_sorted = sorted(aggregated_events.values(), key=lambda e: e.date)


# ==============================
# 5. Calculate Principal Balances, Days Count & Interest
# ==============================

principal_balance = 0
interest_balance = 0
current_interest_rate = 0.0  # Default interest rate

for i, event in enumerate(events_list_date_aggregated_sorted):
    # Check if there was an interest rate update on this date
    for raw_event in events_list_raw:
        if datetime.strptime(raw_event["date"], "%Y-%m-%d") == event.date and "interest_rate" in raw_event:
            current_interest_rate = raw_event["interest_rate"]

    # Update principal balance
    principal_balance += event.principal_lending + event.capitalization - event.repayment + event.principal_balance_correction
    event.principal_balance = principal_balance  

    # Calculate days_count (difference between next event date and current date)
    if i < len(events_list_date_aggregated_sorted) - 1:
        next_event = events_list_date_aggregated_sorted[i + 1]
        event.days_count = (next_event.date - event.date).days
    else:
        event.days_count = 0  # Last event has no next date

    # Calculate interest accrued
    event.interest_accrued = (current_interest_rate / 365) * event.days_count * event.principal_balance

    # Update interest balance
    interest_balance += event.interest_accrued
    event.interest_balance = interest_balance


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