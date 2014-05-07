kairos_sentiment
================

Sentiment analyzer for streaming twitter into KairosDB (with Cassandra) using Alchemy API


The Basics

  Stream twitter firehose, choosing to filter OR sample by both user and term.

Some more in-depth

  I originally started looking through TWEEPY and TWYTHON.  I chose tweepy simply because it worked really quick and this was all started as a hack, not a serious project.  The code is still there for both, but I would recommend using tweepy as I did.
  
  I really should make a configuration file that contains all the keys, secrets, etc... that you'll require to run this and allow it to just be included where it needs to be.  That's very easy to do, but I'm being lazy about it.
  
  I used several animated matplotlib examples and hacked away at them.  I finally settled and stuck some code (of my own) into pandas.py, although it's really not a subplots animation at all.  It gives you ONE static graph when you call it.
  
  This was overall more about messing around with matplotlib (since it had been a while), doing some animations with it and learning about pandas (since I really like R).

TO-DO:

  Figure out how to animate the pandas dataframes that get retunred.  I messed around with it for a few hours, couldn't quite figure it out, so I left it, since the KairosDB GUI provides graphing for what I wanted anyway.  I urge someone to educate me about how to do that if they know (couldn't find an answer).
  
  I would assume it has something to do with manipulating different Axes subplots, but I didn't really look into it.

INSTALL

Tweepy
  https://github.com/tweepy/tweepy
  
Numpy/Scipy/Pandas/Matplotlib 
  http://www.scipy.org/install.html
  
CCM
 https://gist.github.com/vanjos/6169734

KairosDB
  https://code.google.com/p/kairosdb/wiki/GettingStarted

Register for some API KEYS
  https://apps.twitter.com/
  http://www.alchemyapi.com/api/register.html

Things you'll need to configure:

twitter/stream_tweepy.py

  Line 11-15
    ### PUT IN YOUR TWITTER APP API KEYS ###
    ckey = "YOUR CONSUMER KEY"
    csecret = "YOUR CONSUMER SECRET"
    atoken = "YOUR ACCESS TOKEN"
    asecret = "YOUR ACCESS SECRET"
  
  Line 171 - 173
    ### YOU NEED TO CHANGE THIS TO YOUR KAIROS INSTALLATION ENDPOINT ###
    PORT = 8080
    BASE_URL    =   'http://localhost:' + str(PORT) + '/api/v1/datapoints'
    
plotters/pandas.py

  Line 30-32 & 47-49
  ### YOU NEED TO CHANGE THIS TO YOUR KAIROS INSTALLATION ENDPOINT ###
  PORT = 8080
  BASE_URL    =   'http://localhost:' + str(PORT) + '/api/v1/' + trailing_url[what]
