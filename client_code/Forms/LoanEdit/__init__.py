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
    # fetch form values
    self.lender_dropdown.items = anvil.server.call('fetch_companies_dropdown')
    self.borrower_dropdown.items = anvil.server.call('fetch_companies_dropdown')
    self.interest_rate_base_dropdown.items = anvil.server.call('get_interest_rate_bases')
    self.base_currency_ticker_dropdown.items = anvil.server.call('get_currency_ticker')
    # populate foem values
    self.item = anvil.server.call('fetch_loan_info')   
    self.interest_rate_type_radio_group_panel.selected_value = self.item['interest_rate_type']

  """
  def clear_inputs(self):
    self.lender_box.text = ""
    self.borrower_box.text = ""
    self.description_box.text = ""
    #self.base_currency_ticker_dropdown = ""
    #self.interest_rate_base_dropdown = ""
    self.lending_date_exclusive_counting_checkbox.checked = False
    self.repayment_date_exclusive_counting_checkbox.checked = True
    self.capitalization_checkbox.checked = False

  def save_button_click1(self, **event_args):
    # This method is called when the button is clicked
    lender = self.lender_box.text
    borrower = self.borrower_box.text
    description = self.description_box.text
    base_currency = self.base_currency_ticker_dropdown.selected_value
    interest_rate_base = self.interest_rate_base_dropdown.selected_value
    lending_date_exclusive_counting = self.lending_date_exclusive_counting_checkbox.checked
    repayment_date_exclusive_counting = self.repayment_date_exclusive_counting_checkbox.checked
    capitalization = self.capitalization_checkbox.checked
    anvil.server.call('add_loan',
                      lender,
                      borrower,
                      description,
                      base_currency,
                      interest_rate_base,
                      lending_date_exclusive_counting,
                      repayment_date_exclusive_counting,
                      capitalization)
    #alert('Feedback submited')
    Notification('Loan saved').show()
    self.clear_inputs()
  """
    
