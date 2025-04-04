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

class Loans(LoansTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.layout.loans_nav_link.selected = True

    # Any code you write here will run before the form opens.

  def add_loan_button_click(self, **event_args):
    """This method is called when the component is clicked."""
    alert(content = LoanEdit())
