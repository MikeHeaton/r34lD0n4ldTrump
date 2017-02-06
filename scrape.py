# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 2016

@author: Mike Heaton, Andrea Heyman
"""

import re
import twitter_connect
import json
import pandas as pd
import numpy as np
from config import PARAMS
from sklearn.preprocessing import normalize
from collections import defaultdict, Counter

class TweetModel:
    def __init__(self, data, screenname=None):
        # Data is a list of tweets as strings.
        self.screenname = None
        self.process_tweets(data)

    def process_tweets(self, data):
        # Split the string data into word tokens
        print("- Splitting data")
        split_data = [string_to_list(tweetclean(tweet)) for tweet in data]
        self.bigram_successors = defaultdict(list)

        print("- Sequencing bigrams")
        # Pass through the data once to list the words and bigrams, and count successors.
        for words in split_data:
            self._sequencebigrams(words)

        self.bigram_successors = {x: Counter(self.bigram_successors[x]) for x in self.bigram_successors.keys()}

    def _sequencebigrams(self, wordlist):
        # Takes a list of wordgrams. Looks at the bigrams and words in the
        # list and encodes them into the dictionaries bigram_mappings,
        # decode_dict and word_mappings.

        # bigram_counter and word_counter keep track of what variable to assign
        # to a new, unseen gram.

        self.bigram_successors[wordlist[0]].append(wordlist[1])

        for i in range(len(wordlist)-2):
            self.bigram_successors[(wordlist[i], wordlist[i+1])].append(wordlist[i+2])

    """
            self.encode_bigram = {"__START__": 0}
            self.bigram_counter = 1
            self.encode_word = {"__START__": 0, "__END__": 1}
            self.word_counter = 2
            self.decode_dict = {0: "__START__", 1: "__END__"}


            if (wordlist[i], wordlist[i+1]) not in self.encode_bigram:
                self.encode_bigram[(wordlist[i], wordlist[i+1])] = self.bigram_counter
                self.bigram_counter += 1
            if wordlist[i+1] not in self.encode_word:
                self.encode_word[wordlist[i+1]] = self.word_counter
                self.decode_dict[self.word_counter] = wordlist[i+1]
                self.word_counter += 1"""

def tweetclean(s):
    # Take a unicode string of a tweet
    # Strip out emojis and returns them separately
    # Strip out URLs into a 'url' token
    # Tokenise all @names into a 'name' token
    # Triple+ characters are misspellings - make them double
    #           (to catch hellooooooo etc

    # Delete all URLs because they don't make for interesting tweets.
    s = re.sub(r'http[\S]*', '', s)

    # Replace some common unicode symbols with raw character variants
    s = re.sub(r'\\u2026', '...', s)
    s = re.sub(r'\\u2019', "'", s)
    s = re.sub(r'\\u2018', "'", s)

    # Delete emoji modifying characters
    s = re.sub(chr(127996), '', s)
    s = re.sub(chr(65039), '', s)

    # Kill apostrophes because they confuse things.
    s = re.sub(r"'", r"", s)
    # Kill quote marks because they produce ugly results.
    s = re.sub(r'"', r"", s)

    return s

def string_to_list(inp):
    # Take an input string, split it into separate words and punctuations.
    # Return them as a list.
    return ["__START__"] + re.findall(r"[\.\,\?\!\:\-\/\"\;]+|[^\s\.\,\?\!\:\-\/\"\;]+", inp) + ["__END__"]

def gentext(models):
    # Iteratively generates a text list by picking successors among the models.
    switchcount = 0
    textlist = ["__START__"]
    currentbigram = "__START__"
    nextword = None
    currentmodel = None

    while nextword != "__END__":
        # Random choice of model, then random choice of word
        nextmodel = np.random.choice([i for i in models.values() if currentbigram in i.bigram_successors])
        successors, freqs = zip(*list(nextmodel.bigram_successors[currentbigram].items()))
        totalfreq = sum(freqs)
        nextword = np.random.choice(successors, p=[f / totalfreq for f in freqs])
        textlist.append(nextword)

        if currentmodel is not None and currentmodel != nextmodel:
            switchcount += 1
        currentmodel = nextmodel
        currentbigram = (textlist[-2], textlist[-1])

    return switchcount, textlist[1:-1]


def cleanupstring(inputlist):
    # Takes a list of strings (words and punctuation), concatenates them
    # into a string, and uses regex to clean up the formatting.
    # Returns the output string.
    s = " ".join(inputlist[1:-1])
    if len(s) == 0:
        return s

    s = re.sub(r'( [a-zA-Z]) . ([a-zA-Z]) .', "\\1.\\2.", s)
    s = re.sub(r' ([\,\.\/\-\"\?\!\:\;])', "\\1", s)
    s = re.sub(r'- ', "-", s)
    s = re.sub(r'([0-9]), ([0-9])', '\\1,\\2', s)
    s = re.sub(r'([0-9]). ([0-9])', '\\1.\\2', s)
    s = re.sub(r'([0-9]): ([0-9])', '\\1:\\2', s)
    s = re.sub(r'&amp;', "&", s)
    if s[-1] == ':':
        s = s[:-1] + '.'

    if s[0] == ':':
        s = s[1:]

    if s[-1] not in list('.?!'):
        s = s + '.'

    s = s[0].upper() + s[1:]
    return s


def makepost(tweet_text, client):
    # Generates text using the global dictionaries previously defined;
    # re-generates until the tweet is below 140 characters. (Approximately
    # half the time based on sampling.)
    # Logs in to Twitter and posts the generated tweet.

    print(tweet_text)

    print("Posting to twitter")
    url = "https://api.twitter.com/1.1/statuses/update.json"
    parameters = {"status": tweet_text}
    response = client.post(url, data=parameters)

    print(response)
    return response


def runall(screennames, min_length = PARAMS.min_length,
                        max_length = PARAMS.max_length):
    # Runs all of the above functions in order: fetches the corpus,
    # Processes and organises the data, generates a tweet and posts
    # it to Twitter.

    print("Fetching, cleaning, splitting samples:")
    twitclient = twitter_connect.Client()

    models = {}
    for name in screennames:
        print("__Processing {}__".format(name))
        print("- Fetching data...")
        tweetdata = twitclient.fetchtweets(screenname=name)
        # print(tweetdata)
        #print(tweetdata.text)
        print("- Initialising model...")
        model = TweetModel(tweetdata.text)

        models[name] = model


    switches, textlist = gentext(models)
    tweet_text = cleanupstring(textlist)
    while len(tweet_text) < min_length or len(tweet_text) > max_length:
        switches, textlist = gentext(models)
        tweet_text = cleanupstring(tweet_text)

    response = makepost(tweet_text, twitclient)
    return response

if __name__=="__main__":
    runall(PARAMS.list_of_usernames, min_length = PARAMS.min_length,
                                     max_length = PARAMS.max_length)
