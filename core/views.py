from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes, renderer_classes
from asgiref.sync import sync_to_async, async_to_sync
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from .renderers import FoodPlanerPostRenderer
from .serializers import FoodPlanerSerializer
from django.http import JsonResponse

import subprocess

# from adrf.decorators import api_view

import requests

from django.conf import settings
from food_planer.settings import OPENAI_API_KEY, ANTHROPIC_API_KEY, DENDRITE_API_KEY
from django.core.exceptions import ImproperlyConfigured

import openai
import json
import asyncio
import dendrite_sdk
import tempfile
from dendrite_sdk import AsyncDendrite
# Create your views here.

from playwright.sync_api import sync_playwright
from pdfminer.high_level import extract_text_to_fp
from urllib.parse import urljoin
from io import BytesIO
import os

if OPENAI_API_KEY:
    openai.api_key = os.environ.get('OPENAI_API_KEY')
else:
    raise Exception('OpenAI API Key not found')


# async def async_test_view(request):
#     dendrite_client = dendrite_sdk.AsyncDendrite(dendrite_api_key=DENDRITE_API_KEY,openai_api_key=OPENAI_API_KEY,anthropic_api_key=ANTHROPIC_API_KEY)
#     await dendrite_client.goto("https://google.com")
#     return JsonResponse({'message': 'Hello from async view'})

def sync_test_view(request):
    result = subprocess.run(
        ["python", "/home/karlcf/food_planer/core/dendrite_script.py"], capture_output=True, text=True
    )
    if result.returncode == 0:
        print("This is the result:",result.stdout)
        return JsonResponse({"content": result.stdout})
    else:
        error = result.stderr
        print(error)
        return JsonResponse({"error": "Failed to run Dendrite script as a subprocess"}, status=500)

@api_view(['POST'])
@renderer_classes([JSONRenderer, FoodPlanerPostRenderer])
def food_planer_request(request):
    if request.method == 'POST':
        food_planer_serialized = FoodPlanerSerializer(data=request.data)
        print(request.data)
        print(food_planer_serialized)
        print(food_planer_serialized.is_valid())
        if food_planer_serialized.is_valid():
            latitude = food_planer_serialized.data['latitude']
            longitude = food_planer_serialized.data['longitude']
            distance = food_planer_serialized.data['distance']*1000
            budget = food_planer_serialized.data['budget']
            number_of_dishes = 3
            portions = food_planer_serialized.data['portions']

            all_articles_on_sale_in_the_area = []
            all_offers_per_store = []

            nearby_stores = get_nearest_grocery_stores(latitude,longitude, distance)

            for store in nearby_stores:
                store_url = store['website']
                store_name = store['name']['text']
                print(f'Now checking sale offer links on {store_name} website:', store_url)
                # print(f'First checking for potential disches to make with the ingredients')
                
                #Get html content from google search
                url = store_url
                links = get_buttons_and_links(url)


                ##Checking if the first url has offers on the first page
                try:
                    content_pdf = generate_pdf(url)
                except Exception as e:
                    print(f'Failed to generate PDF from {url}: {e}')
                    index += 1
                    continue
                text_content = pdf_to_text(content_pdf)

                print(f'For url {url}',f'Extracted text: {text_content}')
    

                content_includes_offers = check_for_offers(text_content)

                if content_includes_offers:
                    print(f'\n\nOffers where found on the first page {url}\n\nNow organize the offers into dict')
                    offers_not_found = False
                    unorganized_text_with_offers = text_content
                else:
                    #Now we first search if there are pdf at this first url
                    offers_not_found = True
                    index = int(1)
                    identified_targets_urls = analyze_html_with_llm(links,"urls with grocery sales offer keywords in the link in order where the most likely link to have sales offers first",5) #Return a dict as {"url_1": "the first url", "url_2": "The second"} and so on.
                    identified_targets_pdf_urls = analyze_html_with_llm(links,"pdfs links",5) #Return a dict as {"url_1": "the first url", "url_2": "The second"} and so on.
                    
                    # print('this is the identified targets:', identified_targets_urls)
                    # print('this is the identified pdf targets:', identified_targets_pdf_urls)
                    print(f'Number of potential sale offer links found: {len(identified_targets_urls)}\n\nNow itterate through sale offer pages to check for actual offers')
                    identified_targets_urls = json.loads(identified_targets_urls)
                    while offers_not_found and index < 3:
                        try:
                            test_url = identified_targets_urls[f"url_{index}"]
                        except KeyError:
                            print('No more urls to test so no Offers where found on their page')
                            break

                        try:
                            content_pdf = generate_pdf(test_url)
                        except Exception as e:
                            print(f'Failed to generate PDF from {test_url}: {e}')
                            index += 1
                            continue
                        text_content = pdf_to_text(content_pdf)

                        print(f'For url {test_url}',f'Extracted text: {text_content}')
            

                        content_includes_offers = check_for_offers(text_content)

                        if content_includes_offers:
                            print(f'\n\nOffers where found on the page {test_url}\n\nNow organize the offers into dict')
                            offers_not_found = False
                            unorganized_text_with_offers = text_content

                        index += 1


                dict_with_offers = organize_offers(unorganized_text_with_offers)
            
                all_articles_on_sale_in_the_area.extend(dict_with_offers["offers"].keys())
                # print('this is the dict with offers:', dict_with_offers)
            

                store_product_prices = {f'{store_name}': 
                dict_with_offers["offers"]
    }
                all_offers_per_store.append(store_product_prices)
            #########################################
            #######

            print('\n\nNow we have all articles on sale in the area and the prices of the articles in the stores.\n\n Now we give suggestions on possible dishes that can be made:')
            # Now we have all articles on sale in the area and the prices of the articles in the stores.

            dishes = []
            print('this is the all offers per store:', len(all_offers_per_store))
            while len(dishes) < number_of_dishes:

                for store_offers in all_offers_per_store:
                    if len(store_offers.values()) == 0:
                        continue
                
                    print(f'Now giving  a dish suggestion from the store: {store_offers}')
                    store_name = list(store_offers.keys())[0]
                    #Store offers is a dict
                    # Create dish_suggestions
                    client = openai.OpenAI(api_key=OPENAI_API_KEY)


                    dish_sugestions = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        max_tokens=256*4, 
                        n=1, 
                        stop=None, 
                        temperature=0.5,
                        messages=[ 
                        {"role": "system", "content": [{"type": "text", "text": "You are an diner sugesttions assistan. You are helping a user find cheap alternatives for dishes based on existing sales prices."}]},
                        {"role": "user", "content": [{"type": "text", "text": f"Here are the articles and with their orignal and reduced price as a dict for a store:{store_offers} ."}]},
                        {"role": "user", "content": [{"type": "text", "text": f"Do not schoos a dish that is already in this list: {dishes}."}]},
                        {"role": "system", "content": [{"type": "text", "text": """Now give the user 1 suggestions for a dish that will use as many products as possible from the sales lists. Only answer with the name of the dish."""}]},

                    ]
                    
                    )

                
                
                    dish_sugestion_response = dish_sugestions.choices[0].message.content
                    print('this is the dish sugestions:', dish_sugestion_response)
                    dishes.append((store_name,dish_sugestion_response))

                    print("This is the number of suggested dishes",len(dishes), number_of_dishes)

                    if len(dishes) == number_of_dishes:
                        break



                
            

            return Response({'store_offers': all_offers_per_store, "dish_suggestions": dishes}, status=200)


    ### THIS SHOULD BE A SEPRATE API CALL    
# for dish in dishes:
#                 print('this is the store:', store)
#                 client = openai.OpenAI(api_key=OPENAI_API_KEY)


#                 ingredients_creator = client.chat.completions.create(
#                     model="gpt-3.5-turbo",
#                     max_tokens=256, 
#                     n=1, 
#                     stop=None, 
#                     temperature=0.5,
#                     response_format= { "type": "json_object" },
#                     messages=[ 
#                     {"role": "system", "content": [{"type": "text", "text": "You are an food shopping assistant. You are helping a user to come up with different disches that can be done given a list of grocery articles."}]},
#                     {"role": "system", "content": [{"type": "text", "text": "As many ingredients as possible should be used from these: " + str(all_articles_on_sale_in_the_area)}]},
#                     {"role": "user", "content": [{"type": "text", "text": f"Give me a max of 2 dishes."}]},
#                     {"role": "system", "content": [{"type": "text", "text": """Now give the user the list of ingredients that they need to buy for the dish in a json format with the following keys and values: {"dish_1": "List with ingridents for dish 1"} and add more dishes if needed."""}]},
#                     ]
                
#                 )

#                 ingredients_creator_response = ingredients_creator.choices[0].message.content

#                 ingredients_json = json.loads(ingredients_creator_response)

# client = openai.OpenAI(api_key=OPENAI_API_KEY)


#             cheapest_grocery_store = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 max_tokens=256*4, 
#                 n=1, 
#                 stop=None, 
#                 temperature=0.5,
#                 messages=[ 
#                 {"role": "system", "content": [{"type": "text", "text": "You are an food shopping calculator assistant. You are helping a user find the best grocery store to buy ingredients for a dish based on the ingredients and the current sales prices."}]},
#                 {"role": "system", "content": [{"type": "text", "text": "The user wants to buy ingredients for a dish. They want to buy the following ingredients: " + str(dish_1_recepie)}]},
#                 {"role": "user", "content": [{"type": "text", "text": f"Here are the current prices for each nerby store {product_prices_per_store}."}]},
#                 {"role": "system", "content": [{"type": "text", "text": """Now give the user the information about the cheapest grocery store to buy the ingredients from and the total price of the ingredients."""}]},
#                ]
            
#             )

#             shopping_plan = cheapest_grocery_store.choices[0].message.content

            









###################################################################################
## Now the logic goes like this:

# 1. The user sends a POST request to the /food_planer endpoint.
# This give information about what the user wants to eat for dish.


#2. With this information we want to use an llm endpoint to write out all the ingridients that is needed for the dishes.
# Then the user should be able remove or add ingredients to the list.

# 3. while the user is removing or adding ingredients we use dendrite to search for sales on grocerys in the area.
# This is done by searcinh for nearby grocery store using google maps api.
# First we need to find the 5 closest grocery stores to the user. Then we need to find the sales on the ingredients that the user wants to buy.
# When we used dendrite to find these we convert their sales documents into strctured data that we can use to compare the prices of the ingredients.


# 4. When we have the prices of the ingredients we can compare them to find the cheapest grocery store to buy the ingredients from.
# We send the user the information about the cheapest grocery store and the total price of the ingredients togheter with a list of the ingredients that the user wants to buy with a motivation why that store was choosen.



# 5. The user can then choose to buy the ingredients from the store or not.
# This is also done using dendrite. We send the user the information about the store and the user can then choose to buy the ingredients from the store or not.



def get_nearest_grocery_stores(latitude, longitude, radius=3000, max_result_count=3):

    # Construct the request payload
    request_payload = {
        "includedTypes": ["grocery_store","supermarket"],
        "maxResultCount": max_result_count,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius
            }
        }
    }

    # Set up the API request URL and headers
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': settings.GOOGLE_MAPS_API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.formattedAddress,places.types,places.websiteUri'
    }

    # Make the request to the Google Places API
    response = requests.post(url, headers=headers, json=request_payload)
    print('this is the response:', response.json())
    
    # Parse the response and extract the grocery store data
    grocery_stores = []
    for place in response.json().get('places', []):
        grocery_stores.append({
            'name': place.get('displayName', ''),
            'address': place.get('formattedAddress', ''),
            'types': place.get('types', []),
            'website': place.get('websiteUri', ''),
            'price_level': place.get('priceLevel', ''),
            'rating': place.get('rating', ''),
        })
    
    print('these are the nearby stores:', grocery_stores)
    return grocery_stores


async def google_search_recepie(client, query: str):

    # Navigate with the `goto` method
    await client.goto("https://google.com")

    # # Populate the search field
    # await client.fill("Search input field","hello world")


    # await client.extract("Get the first url from the search results")

    #  # Navigate with `goto`, which returns a 'DendritePage' that controls the current page.
    # page = client.goto("https://google.com")

    # # Get elements from the current page with `get_element`.
    # search_bar = page.get_element("The search bar")
    
    # # Let's enter the search query into the search bar.
    # search_bar.fill(query)

    # # Press enter to search
    # page.keyboard.press("Enter")

    # # Wait for the page to load

    # first_url =  page.extract(
    #     "Get the first url from the search results"
    # )

    # print('this is the first url:', first_url)
    

    # # Navigate with `goto`, which returns a 'DendritePage' that controls the current page.
    # page =  client.goto("https://google.com")

    # # Get elements from the current page with `get_element`.
    # search_bar =  page.get_element("The search bar")
    
    # # Let's enter the search query into the search bar.
    #  search_bar.fill(query)

    # # Press enter to search
    #  page.keyboard.press("Enter")

    # # Wait for the page to load

    # first_url =  page.extract(
    #     "Get the first url from the search results"
    # )

    # print('this is the first url:', first_url)


def download_file(url, download_path):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(url)

        # Wait for elements to load
        page.wait_for_timeout(2000)  # Adjust the timeout as necessary

        potential_links = page.query_selector_all('a')  # Modify selector as needed


        
        for link in potential_links:
            # Print the text content and href attribute
            text_content = link.inner_text()
            href = link.get_attribute('href')
            print(f'Text: {text_content}, Href: {href}')


def get_buttons_and_links(url):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()

        # Navigate to the specified URL
        page.goto(url)

        # Get all anchor elements
        links = page.query_selector_all('a')  

        # Use urljoin to ensure full URLs
        extracted_links = [urljoin(url, link.get_attribute('href')) for link in links if link.get_attribute('href')]

        # Close the browser context and browser
        context.close()
        browser.close()

    print("Here are extracted links:", extracted_links)

    return extracted_links


def analyze_html_with_llm(search_content, target, max_results):
    openai.api_key = OPENAI_API_KEY  # Replace with your OpenAI API key
    client = openai.OpenAI()
    print('THIS IS THE LENGTH OF THE SEARCH CONTENT:', len(str(search_content)))
    prompt = f"Analyze the following html_content: {search_content} and find {target}. Write out the {max_results} most fitting targets."
    
    response = client.chat.completions.create(
                model="gpt-4o",
                max_tokens=256*4, 
                n=1, 
                stop=None, 
                temperature=0.5,
                response_format= { "type": "json_object" },
                messages=[
                    {"role": "system", "content": [{"type": "text", "text": prompt}]},
                    {"role": "system", "content": [{"type": "text", "text": f'Maximum number of results to find: {max_results} so choose wisely'}]},
                    {"role": "system", "content": [{"type": "text", "text": """Now answer in a json format with the target keys and their values {"url_1": "the first url", "url_2": "The second"} and so on."""}]},
                ]
            )
    
    print('this is the response:', response)
    # Extract the LLM's response
    return response.choices[0].message.content

def extract_selectors(llm_response):
    lines = llm_response.splitlines()
    selectors = [line for line in lines if line.startswith('.') or line.startswith('#')]
    return selectors


def click_download(url, selectors):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Navigate to the URL
        page.goto(url)

        # Try clicking on each selector found by the LLM
        for selector in selectors:
            try:
                page.click(selector)
                print(f'Clicked on {selector}')
                break  # Exit after clicking the first successful link
            except Exception as e:
                print(f'Failed to click on {selector}: {e}')

        # Wait for the download to complete
        context.close()
        browser.close()



def generate_pdf(url):
    with sync_playwright() as p:
        # Launch a browser
        browser = p.chromium.launch()
        # Create a new page
        page = browser.new_page()
        # Navigate to the URL
        page.goto(url)
        
        page.wait_for_timeout(2000)  # Adjust the timeout as necessary

        # Create a temporary file to hold the PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            # Generate the PDF into the temporary file
            page.pdf(path=temp_file.name, format='A4')
            # Read the PDF content into a BytesIO stream
            pdf_stream = BytesIO()
            with open(temp_file.name, 'rb') as f:
                pdf_stream.write(f.read())
        
        # Close the browser
        browser.close()
        
        # Seek to the beginning of the stream to read its content
        pdf_stream.seek(0)
        return pdf_stream

def pdf_to_text(pdf_stream):
    # Use pdfminer to extract text from the BytesIO stream
    output_string = BytesIO()
    extract_text_to_fp(pdf_stream, output_string)
    # Get the extracted text
    return output_string.getvalue().decode('utf-8')


def check_for_offers(text_content):
    openai.api_key = OPENAI_API_KEY  # Replace with your OpenAI API key
    client = openai.OpenAI()

    response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=256*4, 
                n=1, 
                stop=None, 
                temperature=0.5,
                response_format= { "type": "json_object" },
                messages=[
                    {"role": "system", "content": [{"type": "text", "text": f'Analyze the following text: {text_content} and find if there are any sales offers where both articles and their prices.'}]},
                    {"role": "system", "content": [{"type": "text", "text": """Now answer in a json format with boolean values wheter there are any sales offers or not {"sales_offers_exists": "Boolean True or False wheter sales offers exists in the text"}."""}]},
                ]
            )
    
    print('this is the response:', response)

    response = response.choices[0].message.content
    response = json.loads(response)
    return response['sales_offers_exists']


def organize_offers(unorganized_text_with_offers):
    openai.api_key = OPENAI_API_KEY  # Replace with your OpenAI API key
    client = openai.OpenAI()

    dict_example = """offers = {
    "Steak 1Kg": (159.0, 119.00),
    "Juice (500 ml)": (49.0, 29.00),
    "suasages (300 g)": (45.0, 39.95),
}
"""
    response = client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=256*4, 
                n=1, 
                stop=None, 
                temperature=0.5,
                response_format= { "type": "json_object" },
                messages=[
                    {"role": "system", "content": [{"type": "text", "text": f'You are a professional organizer that goes through a big cunk of text where grocery products are specified with reduced prices and their regular prices.'}]},
                    {"role": "system", "content": [{"type": "text", "text": f'You are to organize the text into a dict with the following this example structure: {dict_example}'}]},
                    {"role": "user", "content": [{"type": "text", "text": f'Organize the following text: {unorganized_text_with_offers}'}]},
                    {"role": "system", "content": [{"type": "text", "text": """Now answer in json format with the following keys and values:
                                                     {
                                                        "offers": 
                                                            {"article_info": "reduced price"}
                                                    }."""}]},
                ]
            )
    
    print('this is the response:', response)

    response = response.choices[0].message.content
    response = json.loads(response)
    return response
