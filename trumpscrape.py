# -*- coding: utf-8 -*-
"""
Created on Mon Oct 24 2016

@author: Mike Heaton, Andrea Heyman
"""

import re
import twitter_api_basic
import json
import pandas as pd
import numpy as np
from sklearn.preprocessing import normalize


def fetchsamples(client, screenname="realdonaldtrump"):
    # Takes in a client object from twitter_api_basic file, 
    # and a twitter screen name.
    # Scrapes the last 3200 statuses from the account and returns
    # them in a Pandas DataFrame.
    url = "https://api.twitter.com/1.1/statuses/user_timeline.json"
    parameters = {"language": "en",
                  "screen_name": screenname,
                  "include_rts": False,
                  "count": 200,
                  }

    response = client.twitterreq(url, "GET", parameters)
    responsedict = json.loads(response.text)
    D = [pd.DataFrame.from_dict(responsedict)]
    minid = min(D[-1]['id'])
    parameters['max_id'] = minid

    for i in range(16):
        print(minid)
        response = client.twitterreq(url, "GET", parameters)
        responsedict = json.loads(response.text)
        D.append(pd.DataFrame.from_dict(responsedict))
        minid = min(D[-1]['id'])
        parameters['max_id'] = minid

    return pd.concat(D)


def tweetclean(s):
    s
    # Take a unicode string of a tweet
    # Strip out emojis and returns them separately
    # Strip out URLs into a 'url' token
    # Tokenise all @names into a 'name' token
    # Triple+ characters are misspellings - make them double
    #           (to catch hellooooooo etc

    # Remove all '@'s except @s pointing to realdonaldtrump.
    # This stops us potentially @-referencing random people, except The Donald
    # himself.
    s = re.sub(r'\@(?!realdonaldtrump)', '', s)

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

    return s


def splitstring(inp):
    # Take an input string, split it into separate words and punctuations.
    # Return them as a list.
    return re.findall(r"[\.\,\?\!\:\-\"\;]+|[^\s\.\,\?\!\:\-\"\;]+", inp)


def countbigrams(wordlist):
    # Takes a list of wordgrams. Looks at the bigrams and words in the
    # list and encodes them into the global dictionaries bigram_mappings,
    # decode_dict and word_mappings.

    # bigram_counter and word_counter keep track of what variable to assign
    # to a new, unseen gram.
    global bigram_mappings, bigram_counter, word_mappings, word_counter
    global decode_dict

    wordlist = ["@START"] + wordlist
    for i in range(len(wordlist)-1):
        if bigram_mappings.get((wordlist[i], wordlist[i+1])) is None:
            bigram_mappings[(wordlist[i], wordlist[i+1])] = bigram_counter
            bigram_counter += 1
        if word_mappings.get(wordlist[i+1]) is None:
            word_mappings[wordlist[i+1]] = word_counter
            decode_dict[word_counter] = wordlist[i+1]
            word_counter += 1


def makefreqs(wordlist):
    # Updates the frequency matrix freq to include bigram-unigram mappings
    # for wordlist.

    global bigram_mappings, word_mappings
    global freq

    wordlist = ["@START"] + wordlist + ["@END"]
    freq[0, word_mappings[wordlist[1]]] += 1
    for i in range(len(wordlist)-2):
        x = bigram_mappings[(wordlist[i], wordlist[i+1])]
        y = word_mappings[wordlist[i+2]]
        freq[x, y] += 1


def gentext():
    # Iteratively generates a text list using the probabilities assigned in the
    # freq matrix.

    # Takes no arguments because the matrices and dictionaries used are global.

    textlist = ["@START"]

    nextword = decode_dict[np.random.choice(word_counter, p=freq[0])]
    textlist.append(nextword)

    while nextword != "@END":
        bigramnumber = bigram_mappings[(textlist[-2], textlist[-1])]
        nextword = decode_dict[np.random.choice(word_counter,
                                                p=freq[bigramnumber])]
        textlist.append(nextword)

    return textlist


def cleanupstring(inputlist):
    # Takes a list of strings (words and punctuation), concatenates them
    # into a string, and uses regex to clean up the formatting.
    # Returns the output string.
    s = " ".join(inputlist[1:-1])
    s = re.sub(r'( [a-zA-Z]) . ([a-zA-Z]) .', "\\1.\\2.", s)
    s = re.sub(r' ([\,\.\/\-\"\?\!\:\;])', "\\1", s)
    s = re.sub(r'- ', "-", s)
    s = re.sub(r'([0-9]), ([0-9])', '\\1,\\2', s)
    s = re.sub(r'([0-9]). ([0-9])', '\\1.\\2', s)
    s = re.sub(r'([0-9]): ([0-9])', '\\1:\\2', s)
    s = re.sub(r'&amp;', "&", s)
    if s[-1] == ':':
        s = s[:-1] + '.'
    return s


def makepost(client):
    # Generates text using the global dictionaries previously defined;
    # re-generates until the tweet is below 140 characters. (Approximately
    # half the time based on sampling.)
    # Logs in to Twitter and posts the generated tweet.

    s = cleanupstring(gentext())
    while len(s) > 140:
        s = gentext()

    print(s)
    url = "https://api.twitter.com/1.1/statuses/update.json"
    parameters = {"status": s}

    print("Posting to twitter")
    response = client.twitterreq(url, "POST", parameters)

    print(response)
    return response


def runall():
    # Runs all of the above functions in order: fetches the corpus,
    # Processes and organises the data, generates a tweet and posts
    # it to Twitter.

    global bigram_mappings, bigram_counter, word_mappings, word_counter
    global decode_dict, freq, unnormalisedfreq

    # Initialise the global variables.
    # Using globals is of course sloppy practice but we're doing it anyway
    # because we're confident of the intended use of the code.
    # An alternative would be to pass the variables back and forth between
    # calls of countbigrams and other functions.

    bigram_mappings = {"@START": 0}
    bigram_counter = 1
    word_mappings = {"@START": 0, "@END": 1}
    word_counter = 2
    decode_dict = {0: "@START", 1: "@END"}
    freq = np.zeros([0, 0])

    print("Fetching samples")
    twitclient = twitter_api_basic.Client()
    D = fetchsamples(twitclient)

    print("Cleaning and splitting data")
    D['clean'] = [tweetclean(t) for t in D.text]
    D['split'] = [splitstring(t) for t in D.clean]

    print("Generating bigrams")
    for i in D.split:
        countbigrams(i)
    print("Found {:d} unique bigrams and {:d} unique words".format(
                                                bigram_counter, word_counter))

    print("Populating frequency matrix")
    freq = np.zeros([bigram_counter, word_counter])
    for i in D.split:
        makefreqs(i)

    print("Normalising frequency matrix")
    unnormalisedfreq = freq
    freq = normalize(freq, norm='l1', axis=1)

    print("Generating text")
    makepost(twitclient)
    return 0
