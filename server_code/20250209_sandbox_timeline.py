#!/usr/bin/env python3
from datetime import datetime
from collections import defaultdict

#sample data
events_list_raw=[]
dict1 = {'event_id': 1,'date':'2024-02-01', 'principal_lending':300, 'currency':'USD'}
dict2 = {'event_id': 2,'date':'2024-01-03', 'principal_lending':400, 'currency':'USD'}
dict3 = {'event_id': 3,'date':'2025-02-01', 'principal_lending':120, 'currency':'USD'}
dict5 = {'event_id': 4,'date':'2024-01-03', 'principal_lending':333, 'currency':'USD'} #duplicated date with different event 
dict4 = {'event_id': 5,'date':'2023-02-01', 'principal_lending':66, 'currency':'USD'}
dict6 = {'event_id': 6,'date':'2024-01-04', 'repayment': 113, 'currency':'USD'}
events_list_raw.extend([dict1, dict2, dict3, dict4, dict5, dict6])
#events_list_raw_sorted = sorted(events_list_raw, key=lambda item: item['date'])

# Default data structure (events_list_aggregated_sorted)
default_dict = defaultdict(lambda: {
  'event_id': None,
  'date': None, 
  'principal_lending': 0, 
  'currency': None, 
  'capitalization': 0,
  'repayment':0,
  'principal_balance_correction': 0,
  'principal_balance': 0
  })

# Create a default dictionary by enevt_id with populated values
for item in events_list_raw:
  event_id_key = item['event_id']
  default_dict[event_id_key]['event_id'] = event_id_key
  default_dict[event_id_key]['date'] = datetime.strptime(item['date'], "%Y-%m-%d")
  default_dict[event_id_key]['event_id'] = item.get('event_id', None)
  default_dict[event_id_key]['principal_lending'] = item.get('principal_lending', 0) #helps to aggregate events at the same date
  default_dict[event_id_key]['repayment'] = item.get('repayment', 0)
  default_dict[event_id_key]['currency'] = item.get('currency', None)
events_list_aggregated_sorted = sorted(default_dict.values(), key=lambda item: item['date'])

print("-" * 50)  # Separator line
print(f"{'Date':<12} {'Lending':>8} {'Repayment':>8}")
print("-" * 50)  # Separator line
print(*["{} {:>8} {:>8} ".format(
    item['date'].date(),
    item['principal_lending'],
    item['repayment']
) for item in events_list_aggregated_sorted], sep="\n")
print("-" * 50)  # Separator line


default_dict_date_aggregated = defaultdict(lambda: {
  'date':None, 
  'principal_lending': 0, 
  'currency': None, 
  'capitalization': 0,
  'repayment':0,
  'principal_balance_correction': 0,
  'principal_balance': 0,
  'event_ids': []}) # To keep track of which events were aggregated

#Aggregate transactions by date: sum values for the same date
for event in default_dict.values():
    date_key = event['date']
    default_dict_date_aggregated[date_key]['date'] = date_key
    default_dict_date_aggregated[date_key]['principal_lending'] += event['principal_lending']
    default_dict_date_aggregated[date_key]['repayment'] += event['repayment']
    default_dict_date_aggregated[date_key]['currency'] = event['currency']
    default_dict_date_aggregated[date_key]['event_ids'].append(event['event_id'])

events_list_date_aggregated_sorted = sorted(default_dict_date_aggregated.values(), key=lambda item: item['date'])

print("-" * 50)  # Separator line
print(f"{'Date':<12} {'Lending':>8} {'Repayment':>8} {'Balance':>8} {'Event_ids':>8}")
print("-" * 50)  # Separator line
print(*["{} {:>8} {:>8} {:>8} {:>8}".format(
    item['date'].date(),
    item['principal_lending'],
    item['repayment'],
    item['principal_balance'],
    str(item['event_ids'])
) for item in events_list_date_aggregated_sorted], sep="\n")
print("-" * 50)  # Separator line


#Calculate balances
principal_balance = 0
for item in events_list_date_aggregated_sorted:
  principal_balance +=item['principal_lending']+item['capitalization']-item['repayment']+item['principal_balance_correction']
  item['principal_balance'] = principal_balance


print("-" * 50)  # Separator line
print(f"{'Date':<12} {'Lending':>8} {'Repayment':>8} {'Balance':>8}")
print("-" * 50)  # Separator line
print(*["{} {:>8} {:>8} {:>8}".format(
    item['date'].date(),
    item['principal_lending'],
    item['repayment'],
    item['principal_balance']
) for item in events_list_date_aggregated_sorted], sep="\n")
print("-" * 50)  # Separator line


#Analytical section
def balance_report(data, report_date):
  report_date = datetime.strptime(report_date, "%Y-%m-%d")
  if report_date < data[0]['date']:
    print(0)
    return 0
  previous_balance = 0
  for item in data:
    if item['date']==report_date:
      return item['principal_balance']
    elif item['date']>report_date:
        return previous_balance
    previous_balance = item['principal_balance'] # Always update previous principal_balance
  # If report_date is after all transactions, return last principal_balance
  return previous_balance


print(balance_report(events_list_date_aggregated_sorted,'2024-01-03'))