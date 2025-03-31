from ._anvil_designer import SubscriptionsTemplate
from anvil import *
import anvil.server
import anvil.google.auth, anvil.google.drive
from anvil.google.drive import app_files
import anvil.facebook.auth
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class Subscriptions(SubscriptionsTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)
    user = anvil.users.get_user()
    self.layout.reset_links()
    self.layout.subscriptions_nav_link.selected = True
    #self.subscriptions_panel.items = [{'created_on':'1222'},{'created_on':'333'}]
    self.subscriptions_panel.items = anvil.server.call('fetch_subscriptions', user)
    # Any code you write here will run before the form opens.
