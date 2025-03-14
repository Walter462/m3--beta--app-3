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
    
