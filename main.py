from slack import WebClient
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from yelp.client import Client
import requests


env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)


# Create an events adapter and register it to an endpoint in the slack app for event injestion.
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)

slack_web_client = WebClient(token=os.environ['SLACK_TOKEN'])

BOT_ID = slack_web_client.api_call("auth.test")['user_id']
yelp_web_client = Client(os.environ['YELP_API_KEY'])

headers = {'Authorization': 'Bearer {}'.format(os.environ['YELP_API_KEY'])}
search_api_url = os.environ['API_HOST'] + os.environ['SEARCH_PATH']
default_limit = os.environ['DEFAULT_LIMIT']
default_location = os.environ['DEFAULT_LOCATION']
api_key = os.environ['YELP_API_KEY']
headers = {
    'Authorization': 'Bearer %s' % api_key,
}


def display_search(response, location):
    message = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":tada: I found {} results in {}.\n".format(len(response), location or default_location)
                }
            },
            {
                "type": "divider"
            },
        ]}

    for venue in response:
        categories = []
        if not venue['is_closed']:
            [categories.append(a['title']) for a in venue['categories']]
            section = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*{name} - {rating} :star:* {review_count} reviews\n_{categories}_\n:phone: {phone}\n".format(name=venue['name'], 
                                    rating=venue['rating'], 
                                    review_count=venue['review_count'], 
                                    categories=", ".join(categories), 
                                    phone=venue['display_phone'])
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": venue['image_url'],
                        "alt_text": "alt text for image"
                    }
                }
            message["blocks"].append(section)
    return message
# msg = {
# 	"blocks": [
# 		{
# 			"type": "section",
# 			"text": {
# 				"type": "mrkdwn",
# 				"text": ":tada: I found {} results in {}.\n".format(len(response), location or default_location)
# 			}
# 		},
# 		{
# 			"type": "divider"
# 		},
# 		{
# 			"type": "section",
# 			"text": {
# 				"type": "mrkdwn",
# 				"text": "*{name}> - {rating} :star:* {review_count} reviews\n_{categories}_\n:phone: {phone}\n".format(
#                         name=venue['name'], 
#                         rating=venue['rating'], 
#                         review_count=venue['review_count'], 
#                         categories=", ".join(categories), 
#                         phone=venue['display_phone'])
# 			},
# 			"accessory": {
# 				"type": "image",
# 				"image_url": venue['image_url'],
# 				"alt_text": "alt text for image"
# 			}
# 		},
# 		{
# 			"type": "divider"
# 		},
# 		{
# 			"type": "actions",
# 			"elements": [
# 				{
# 					"type": "button",
# 					"text": {
# 						"type": "plain_text",
# 						"text": venue['image_url'],
# 						"emoji": True
# 					},
# 					"value": "click_me_123",
# 					"url": venue['url']
# 				},
# 			]
# 		}
# 	]
# }

# ========================
params = {'term': 'popcorn chicken',
        'location': 'San Francisco',
        'limit': 2}

response = requests.get(search_api_url, headers=headers, params=params, timeout=5)
# print(response.url)
data = response.json()
print(data['businesses'][1])

# ======================
def search(term, location):
    params = {
        'term': term,
        'location': location or default_location,
        'open_now': True,
        'limit': default_limit
    }

    response = requests.get(search_api_url, headers=headers, params=params)
    return response.json()['businesses']

def display_search1(response, location):
    if not response:
        return ":x: No businesses found."

    message = ":tada: I found {} results in {}.\n".format(len(response), location or default_location)

    i = 1
    for venue in response:
        categories = []
        if not venue['is_closed']:
            [categories.append(a['title']) for a in venue['categories']]
            message += "*{order}. <{yelp_url}|{name}> - {rating} :star:* {review_count} reviews\n_{categories}_\n:phone: {phone}\n".format(order=i, 
                        name=venue['name'], 
                        rating=venue['rating'], 
                        review_count=venue['review_count'], 
                        categories=", ".join(categories), 
                        phone=venue['display_phone'],
                        yelp_url=venue['url'])
            i += 1
    return message

@slack_event_adapter.on('message')
def handle_message(payload):
    event = payload.get('event', {})
    user_id = event.get('user')
    channel_id = event.get('channel')
    text = event.get('text')

    default_message = "I'm sorry. I don't understand. Please type *help* to see all commands."
    message = None
    if "hi" or "hello" in text.lower():
        message = "Hello <@%s>! :wave:" % user_id

    if "help" in text.lower():
        slack_web_client.chat_postMessage(channel=channel_id, **msg)

    if "search" in text.lower():
        user_response = text[6:].split(",")
        location = None
        if len(user_response) > 1:
            location = user_response[1]
        term = user_response[0]
        result = search(term, location)
        message = display_search(result, location)
        slack_web_client.chat_postMessage(channel=channel_id, **message)
        return

    if BOT_ID != user_id:
        slack_web_client.chat_postMessage(channel=channel_id, text=message or default_message)

if __name__ == "__main__":
    app.run(debug=True)
    
    