from ._anvil_designer import LoanEditTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users

class LoanEdit(LoanEditTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.        
    # assign radio buttons to a single group
    self.static_radio_button.group = self.interest_rate_type_radio_group_panel
    self.dynamic_radio_button.group = self.interest_rate_type_radio_group_panel
    if self.item.get('interest_rate_type'):
      self.interest_rate_type_radio_group_panel.selected_value = self.item['interest_rate_type']
    # fetch form values
    self.lender_dropdown.items = anvil.server.call('fetch_companies_dropdown')
    self.borrower_dropdown.items = anvil.server.call('fetch_companies_dropdown')
    self.interest_rate_base_dropdown.items = anvil.server.call('get_interest_rate_bases')
    self.base_currency_ticker_dropdown.items = anvil.server.call('get_currency_ticker')
    # populate foem values
  
      
