from ._anvil_designer import LoansTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ...Forms.LoanEdit import LoanEdit

class Loans(LoansTemplate):
  def __init__(self, **properties):
    # Any code you write here will run before the form opens.
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.layout.loans_nav_link.selected = True
    self.refresh_loans_list()
    self.loans_repeating_panel.set_event_handler('x-delete-loan', self.delete_loan)

  def delete_loan(self, loan, **event_args):
    anvil.server.call('delete_loan', loan)
    
  def refresh_loans_list(self, **event_args):
    self.loans_repeating_panel.items = anvil.server.call('fetch_loans_info')
    
  def add_loan_button_click(self, **event_args):
    """This method is called when the component is clicked."""
    # Initialise an empty dictionary to store the user inputs
    new_loan = { }
    save_cliked = alert(content = LoanEdit(item = new_loan),
         large = True,
         title = 'Loan edit',
         buttons = [("Save", True, "elevated"), ("Cancel", False)])
    if save_cliked:
      anvil.server.call('add_loan', new_loan)
      self.refresh_loans_list()
