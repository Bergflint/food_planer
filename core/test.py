from dendrite_sdk import Dendrite
from food_planner.settings import DENDRITE_API_KEY

# Get your Dendrite API key from dendrite.systems
DENDRITE_API_KEY = DENDRITE_API_KEY

def hello_world():
    # Initate the Dendrite client
    client = Dendrite(dendrite_api_key=DENDRITE_API_KEY)

    # Navigate with the `goto` method
    client.goto("https://google.com")

    # Populate the search field
    client.fill("Search input field","hello world")

hello_world()