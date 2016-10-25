import requests
from requests_oauthlib import OAuth1


class Client():
    def __init__(self,
        api_key="Gl6ybatPrEnDlPA5AHEXfVctR",
        api_secret="4eyCMpemZqZZb193JBmN4OMxxQBR6xLEwCTLf8756teBOkxO9P",
        access_token_key="790661882449461254-GK9wTiFeQQ84J4Ceo17XLoWhnAdJIk3",
        access_token_secret="Lf9iqEiL2TixrQ0jHtbctOHVqSkO7BQ6wa8hSky83wMF0"
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
