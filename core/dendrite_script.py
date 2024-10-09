import dendrite_sdk
from dendrite_sdk import Dendrite, AsyncDendrite 
import asyncio
from food_planner.settings.common import DENDRITE_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY



async def async_dendrite_test():
    dendrite_client = dendrite_sdk.AsyncDendrite(dendrite_api_key=DENDRITE_API_KEY,openai_api_key=OPENAI_API_KEY,anthropic_api_key=ANTHROPIC_API_KEY)
    page = await dendrite_client.goto("https://google.com")
    print("Hello from async function")
    await page.close()
    await dendrite_client.close()
    return {'message': 'Hello from async function'}

def sync_dendrite_test():
    dendrite_client = dendrite_sdk.Dendrite(dendrite_api_key=DENDRITE_API_KEY,openai_api_key=OPENAI_API_KEY,anthropic_api_key=ANTHROPIC_API_KEY)

    dendrite_client.goto("https://google.com")
    return {'message': 'Hello from sync function'}


if __name__ == "__main__":
    url = "https://example.com"
    # content = asyncio.run(async_dendrite_test())
    
    content = sync_dendrite_test()
    print("Content from the dendrite function:",content)  # Do something with the content
