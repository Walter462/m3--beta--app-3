from ._anvil_designer import CompaniesTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class Companies(CompaniesTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.layout.companies_nav_link.selected = True
    # Any code you write here will run before the form opens.
    self.companies_panel.items = anvil.server.call('fetch_companies')

  def clear_cookie_click(self, **event_args):
    """This method is called when the component is clicked."""
    anvil.server.cookies.local.clear()

