from celery import shared_task
from time import sleep
import requests

from gripcontrol import HttpStreamFormat
from django_grip import publish

import openai
import json

from django.conf import settings

@shared_task
def test_task(duration, channel):
    # Simulating a long-running task
    from time import sleep
    print('hello test task 1')
    sleep(duration)

    # Publish a message to the channel

    publish(channel, HttpStreamFormat('event: update\ndata: {"message": "Task completed and SSE sent from task"}\n\n'))


@shared_task
def get_ingredients(store_name, dish_suggestion, offers):

    print(f'Now giving a dish suggestion from the store: {store_name}')
    #Store offers is a dict
    # Create dish_suggestions
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

    ingredients_creator = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        n=1,
        stop=None,
        temperature=0.5,
        response_format= { "type": "json_object" },
        messages=[ 
        {"role": "system", "content": [{"type": "text", "text": "You are an food shopping assistant. You are helping a user to write out the ingredients that is needed for a dish."}]},
        {"role": "system", "content": [{"type": "text", "text": f"The user wants to make {dish_suggestion}. They want to use as many ingredients as possible from this list: " + str(offers)}]},
        {"role": "user", "content": [{"type": "text", "text": f"Write out the ingredients that is needed for the dish {dish_suggestion}."}]},
        {"role": "system", "content": [{"type": "text", "text": """Now give the user the list of ingredients that they need to buy for the dish in a json format with the following keys and values: {"ingredients": "List with ingridents for"}."""}]},
        ]
    )

    ingredients_response = ingredients_creator.choices[0].message.content

    ingredients_json = json.loads(ingredients_response)

    print('this is the ingredients:', ingredients_json)

    return ingredients_json