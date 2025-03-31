from ._anvil_designer import MainLayout_RailsTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class MainLayout_Rails(MainLayout_RailsTemplate):
  def __init__(self, **properties):
    #anvil.users.login_with_form()
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.layout.show_sidesheet = False
    # Any code you write here will run before the form opens.

  def navigation_link_3_click(self, **event_args):
    """This method is called when the component is clicked"""
    anvil.users.logout()
    anvil.open_form('LoggedOut_screen')
