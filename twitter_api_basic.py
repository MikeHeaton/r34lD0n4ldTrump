import requests
from requests_oauthlib import OAuth1


class Client():
    def __init__(self,
        api_key="REDACTED",
        api_secret="REDACTED",
        access_token_key="REDACTED",
        access_token_secret="REDACTED"
                 ):

        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token_key = access_token_key
        self.acces_token_secret = access_token_secret

    def twitterreq(self, url, method, parameters):
        auth = OAuth1(self.api_key, self.api_secret,
                      self.access_token_key, self.access_token_secret)
        if method == "POST":
            response = requests.post(url, data=parameters, auth=auth)
        elif method == "GET":
            response = requests.get(url, params=parameters, auth=auth)
        else:
            print("Invalid method call")

        return response
