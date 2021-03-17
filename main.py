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

# def search(item):
headers = {'Authorization': 'Bearer {}'.format(os.environ['YELP_API_KEY'])}

params = {'term': 'popcorn chicken',
        'location': 'San Francisco',
        'limit': 2}
search_api_url = 'https://api.yelp.com/v3/businesses/search'

response = requests.get(search_api_url, headers=headers, params=params, timeout=5)
# print(response.url)
data = response.json()
print(data['businesses'][1]['review_count'])

# ======================
class Event:
    def __init__(self, term):
        self.term = term
        self.search_api_url = os.environ['SEARCH_API_URL']
        self.default_location = os.environ['DEFAULT_LOCATION']
        self.api_key = os.environ['YELP_API_KEY']
        self.headers = {
            'Authorization': 'Bearer %s' % self.api_key,
        }

    def search(self):
        params = {
            'term': self.term,
            'location': self.default_location,
            'open_now': True,
            'limit': 5
        }

        response = requests.get(self.search_api_url, headers=self.headers, params=params)
        return self.display_search(response.json()['businesses'])
    
    def display_search(self, response):
        message, i = "", 0
        for venue in response:
            categories = []
            if not venue['is_closed']:
                [categories.append(a['title']) for a in venue['categories']]
                message += "{name} - {rating} :star: {review_count} reviews Categories: {categories} Yelp: {yelp_url} \n".format(name=venue['name'], rating=venue['rating'], review_count=venue['review_count'], categories=", ".join(categories), yelp_url=venue['url'])
        return message
    
    def change_location(self, location):
        self.default_location = location


@slack_event_adapter.on('message')
def handle_message(payload):
    event = payload.get('event', {})
    user_id = event.get('user')
    channel_id = event.get('channel')
    text = event.get('text')

    if "hi" or "hello" in text.lower():
        message = "Hello <@%s>! :wave:" % user_id

    if "search" in text.lower():
        term = Event(text[6:])
        message = term.search()
    
    if "set location" in text.lower():
        term = Event(text[12:])
        term.change_location(term)
        message = 'Your default location has been set to: ' + text[12:]
    
    if BOT_ID != user_id:
        slack_web_client.chat_postMessage(channel=channel_id, text=message)



@app.route('/crave', methods=['GET', 'POST'])
def crave():
    return Response(), 200

if __name__ == "__main__":
    app.run(debug=True)