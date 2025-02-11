#!/usr/bin/env python3
from datetime import datetime
from collections import defaultdict

#sample data
events_list_raw=[]
dict1 = {'date':'2024-02-01', 'principal_lending':300, 'Currency':'USD'}
dict2 = {'date':'2024-01-03', 'principal_lending':400, 'Currency':'USD'}
dict3 = {'date':'2025-02-01', 'principal_lending':120, 'Currency':'USD'}
dict5 = {'date':'2024-01-03', 'principal_lending':333, 'Currency':'USD'} #duplicated date with different event 
dict4 = {'date':'2023-02-01', 'principal_lending':66, 'Currency':'USD'}
dict6 = {'date':'2024-01-04', 'repayment': 113, 'Currency':'USD'}
events_list_raw.extend([dict1, dict2, dict3, dict4, dict5, dict6])
#print (*events_list_raw, sep = "\n")
#print('---')
events_list_raw_sorted = sorted(events_list_raw, key=lambda item: item['date'])
print (*events_list_raw_sorted, sep = "\n")
print('---')
#Create deafault data structure
default_dict = defaultdict(lambda: {'date':None, 
                                  'principal_lending': 0, 
                                  'capitalization': 0,
                                  'principal_balance_correction': 0,
                                  'Currency': None, 
                                  'repayment':0})
#Aggregate transactions by date: sum values for the same date
for item in events_list_raw:
  date_key = datetime.strptime(item['date'], "%Y-%m-%d")
  default_dict[date_key]['principal_lending'] += item.get('principal_lending', 0) #helps to aggregate events at the same date
  default_dict[date_key]['repayment'] += item.get('repayment', 0)
  default_dict[date_key]['date'] = date_key
events_list_date_aggregated_sorted = sorted(default_dict.values(), key=lambda item: item['date'])
print(*events_list_date_aggregated_sorted, sep = "\n")
print('---')

principal_balance = 0
for item in events_list_date_aggregated_sorted:
  principal_balance +=item['principal_lending']+item['capitalization']+item['principal_balance_correction']-item['repayment']
  item['principal_balance'] = principal_balance

print(*events_list_date_aggregated_sorted, sep = "\n")
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

