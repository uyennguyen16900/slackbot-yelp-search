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

class WelcomeMessage():
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                'Welcome to this channel! \n\n'
                'Get started by completing the steps below.'
            )
        }
    }

    DIVIDER = {'type': 'divider'}

    def __init__(seld, channel, user):
        self.channel = channel
        self.user = user
        self.icon_emoji = ':robot_face'
        self.timestamp = ''
        self.completed = False
    
    def get_messgae(self):
        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'icon_emoji': self.icon_emoji,
            'block': [ 
                self.START_TEXT,
                self.DIVIDER,
                *self._get_reaction_task()
            ]
        }
    
    def _get_reaction_task(self):
        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark = ':white_large_square:'

        text = f'{checkmark} * Add an emoji reaction to this.'

        return [{'type': 'section', 'text': {'type': 'mrkdwn', 'text': text}}]


def display_search(response, location):
    if not response:
        return ":x: No businesses found."

    message = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":tada: I found {} results in {}.\n".format(len(response), location or default_location)
                }
            },
        ]}

    for venue in response:
        categories = []
        if not venue['is_closed']:
            [categories.append(a['title']) for a in venue['categories']]
            divider = {
                    "type": "divider"
                }

            trans = ":heavy_check_mark:" + " Takeout"
            if "delivery" in venue['transactions']:
                trans += " :heavy_check_mark: " + "Delivery"

            section = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*{name}* - {rating} :star: {review_count} reviews\n_{categories}_\nPhone: {phone}\n{trans}\n".format(
                                name=venue['name'], 
                                rating=venue['rating'], 
                                review_count=venue['review_count'],
                                categories=", ".join(categories), 
                                phone=venue['display_phone'],
                                trans=trans)
                    },
                    "accessory": {
                        "type": "image",
                        "image_url": venue['image_url'],
                        "alt_text": "alt text for image"
                    }
                }
            
            location = {
                    "type": "context",
                    "elements": [
                        {
                            "type": "image",
                            "image_url": "https://api.slack.com/img/blocks/bkb_template_images/tripAgentLocationMarker.png",
                            "alt_text": "Location Pin Icon"
                        },
                        {
                            "type": "plain_text",
                            "emoji": True,
                            "text": ", ".join(venue['location']['display_address'])
                        }
                    ]
                }

            button = {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Go to Yelp",
                                "emoji": True
                            },
                            "value": "click_me_123",
                            "url": venue['url']
                        },
                    ]
                }
            
            for item in [divider, section, location, button]:
                message["blocks"].append(item)

    return message
# ========================
params = {'term': 'popcorn chicken',
        'location': 'San Francisco',
        'limit': 2}

response = requests.get(search_api_url, headers=headers, params=params, timeout=5)
# print(response.url)
data = response.json()
print(data['businesses'][1]['price'])

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

def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    response = slack_web_client.chat_postMessage(**message)
    welcome.timestamp = response['ts']

@slack_event_adapter.on('message')
def handle_message(payload):
    event = payload.get('event', {})
    user_id = event.get('user')
    channel_id = event.get('channel')
    text = event.get('text')

    default_message = "I'm sorry. I don't understand. Please type *help* to see all commands."
    message = None

    if user_id != None and BOT_ID != user_id:
        if text.lower() in ['hello', 'hi', 'hey']:
            message = "Hello <@%s>! :wave:" % user_id

        if "help" in text.lower():
            slack_web_client.chat_postMessage(channel=channel_id, **msg)

        if "search" in text.lower():
            user_response = text[6:].split(", ")
            location = None
            if len(user_response) > 1:
                location = user_response[1]
            term = user_response[0]
            result = search(term, location)
            message = display_search(result, location)
            slack_web_client.chat_postMessage(channel=channel_id, **message)
            return

        if "set location" in text.lower():
            change_location(text[13:])
            message = "you changed location"

        slack_web_client.chat_postMessage(channel=channel_id, text=message or default_message)

if __name__ == "__main__":
    app.run(debug=True)
    
    