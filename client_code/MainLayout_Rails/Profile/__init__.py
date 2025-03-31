from ._anvil_designer import ProfileTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class Profile(ProfileTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    self.layout.reset_links()
    self.layout.profile_nav_link.selected = True
    if anvil.users.get_user() is not None:
      self.item = anvil.server.call('fetch_user_info')
    else:
      anvil.open_form('LoggedOut_screen')

    # Any code you write here will run before the form opens.
