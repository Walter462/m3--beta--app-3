from ._anvil_designer import LoanTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.users

class Loan(LoanTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    # Any code you write here will run before the form opens.
    self.interest_rate_base_dropdown.items = anvil.server.call('get_interest_rate_bases')
    self.base_currency_ticker_dropdown.items = anvil.server.call('get_currency_ticker')
    
  def subscriptionSubmit_btn_click(self, **event_args):
    """This method is called when the component is clicked."""
    name = self.NewLoanDB_name_input_text_box.text
    anvil.server.call("add_subscrition", name)
    alert("New subscription saved successfully")
    self.NewLoanDB_name_input_text_box.text = ""

  def button_1_click(self, **event_args):
    """This method is called when the component is clicked."""
    name = 'Vova'
    anvil.server.call('say_hello', name)
###############################################################
  def clear_inputs(self):
    self.lender_box.text = ""
    self.borrower_box.text = ""
    self.description_box.text = ""
    self.base_currency_ticker_dropdown = ""
    self.interest_rate_base_dropdown = ""
    self.lending_date_exclusive_counting_checkbox = ""
    self.repayment_date_exclusive_checkbox = ""
    self.capitalization_checkbox = ""

  def save_button_click(self, **event_args):
    """This method is called when the button is clicked"""
    lender = self.lender_box.text
    borrower = self.borrower_box.text
    description = self.description_box.text
    base_currency = self.base_currency_ticker_dropdown
    interest_rate_base = self.interest_rate_base_dropdown
    lending_date_exclusive_counting = self.lending_date_exclusive_counting_checkbox
    repayment_date_exclusive_counting = self.repayment_date_exclusive_checkbox
    capitalization = self.capitalization_checkbox
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
    
