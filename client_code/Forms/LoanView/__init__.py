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
    if self.item['contract_start_date']:
      self.contract_start_date_box.text = self.item['contract_start_date'].strftime('%Y-%m-%d')
    # Any code you write here will run before the form opens.

  def edit_loan_button_click(self, **event_args):
    """This method is called when the component is clicked."""
    loan_copy = dict(self.item)
    print(loan_copy)
    save_clicked = alert(content = LoanEdit(item = loan_copy),
         title = "View and edit contract details",
         large = True,
         buttons = [("Save", True), ("Cancel", False)])
    if save_clicked:
      anvil.server.call('update_loan', self.item, loan_copy)
      self.refresh_data_bindings()

  def delete_loan_button_click(self, **event_args):
    """This method is called when the component is clicked."""
    confirm(f"Are you sure you want to delete {self.item['credentials']}?")
    
