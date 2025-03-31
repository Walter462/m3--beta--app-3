from ._anvil_designer import LoggedOut_screenTemplate
from ..MainLayout_Rails import MainLayout_Rails
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class LoggedOut_screen(LoggedOut_screenTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def login_button_click(self, **event_args):
    """This method is called when the component is clicked."""
    anvil.users.login_with_form()
    anvil.open_form('MainLayout_Rails')
    
