from ._anvil_designer import LoanViewTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from ..LoanEdit import LoanEdit

class LoanView(LoanViewTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.refresh_dates()
    # Any code you write here will run before the form opens.
  
  def refresh_dates(self):
    if self.item['contract_start_date']:
      self.contract_start_date_box.text = self.item['contract_start_date'].strftime('%Y-%m-%d')

  def edit_loan_button_click(self, **event_args):
    self.parent.raise_event('x-edit-loan', loan = self.item)
    
  def delete_loan_button_click(self, **event_args):
    """This method is called when the component is clicked."""
    if confirm(f"Are you sure you want to delete {self.item['credentials']}?"):
      self.parent.raise_event('x-delete-loan', loan=self.item)
