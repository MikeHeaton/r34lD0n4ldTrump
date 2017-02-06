"""
By Mike Heaton: www.mike-heaton.com
                github.com/MikeHeaton
Contains the Client class for connnecting to Twitter, and methods
for scraping and posting to Twitter.
"""

import requests
from requests_oauthlib import OAuth1
from config import PARAMS
import pandas as pd

class Client():
    def __init__(self,
                api_key=PARAMS.api_key,
                api_secret=PARAMS.api_secret,
                access_token_key=PARAMS.access_token_key,
                access_token_secret=PARAMS.access_token_secret):

        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token_key = access_token_key
        self.access_token_secret = access_token_secret

    def auth(self):
        return OAuth1(self.api_key,
                        self.api_secret,
                        self.access_token_key,
                        self.access_token_secret)

    def get(self, url, params=None):
        return requests.get(url, params=params, auth=self.auth())

    def post(self, url, data=None):
        return requests.post(url, data=data, auth=self.auth())

    def fetchtweets(self, screenname):
        # Input: a Twitter handle.
        # Fetches all available tweets from the account (max 3200).
        # Returns them in a Pandas dataframe.
        url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
        parameters = {"language": "en",
                      "screen_name": screenname,
                      "include_rts": False,
                      "count": 200,
                      }
        alltweets = pd.DataFrame()

        for i in range(16):
            """TODO: how can I just do this until it breaks?"""
            response = self.get(url, params=parameters)

            response = response.json()
            alltweets = pd.concat([alltweets, pd.DataFrame.from_dict(response)])
            parameters['max_id'] = min(alltweets['id'])

        return alltweets
