#!/usr/bin/env python

import time, sys
from getpass import getpass
from textwrap import TextWrapper
sys.path.insert(0, '../sentiment')
from simplesentiment import Simplesentiment

import tweepy, json

### PUT IN YOUR TWITTER APP API KEYS ###
ckey = "YOUR CONSUMER KEY"
csecret = "YOUR CONSUMER SECRET"
atoken = "YOUR ACCESS TOKEN"
asecret = "YOUR ACCESS SECRET"

class StreamWatcherListener(tweepy.StreamListener):
    """ A listener handles tweets are the received from the stream.
    This is a basic listener that just prints received tweets to stdout.

    """
    status_wrapper = TextWrapper(width=60, initial_indent='    ', subsequent_indent='    ')
    ss          = Simplesentiment()
    denoms      = ss.getDenoms()
    tokenizers  = ss.getTokenizers()
    stemmers    = ss.getStemmers()

    users = []
    filters = []

    def on_status(self, status):
        try:
            print self.status_wrapper.fill(status.text)
            print '\n %s  %s  via %s\n' % (status.author.screen_name, status.created_at, status.source)
        except:
            # Catch any unicode errors while printing to console
            # and just ignore them to avoid breaking application.
            pass

    def on_data(self, data):
        import re, simplejson
        #try:        
        sentiment_score =   0
        sentiment_type  =   ''
        time_queried = int(time.time() * 1000)
        entities = []
        metrics = []

        # let's make sure the tweet is usable as a dict
        data = json.loads(data)
        print 'USERS: ', self.users, ' TERMS: ', self.filters, '\n', data['text'], '\n'

        # sometimes - tweets are ALL hashtags and mentions, no real text
        if data['text']: 
            # we're using AlchemyAPI for entity and sentiment extraction
            alchemyresults = {'sentiment': {}, 'entities': {}}
            alchemyresults['sentiment']  =   self.ss.alchemysentiment({}, re.sub('(^|\s)(http://\S+|[^\w\s",]\S*)','\\1', data['text']).strip())
            alchemyresults['entities']   =   self.ss.alchemyentityextraction({}, re.sub('(^|\s)(http://\S+|[^\w\s",]\S*)','\\1', data['text']).strip())

            print alchemyresults, '\n\n'


            if alchemyresults['sentiment']['status'] == 'OK':
                if 'docSentiment' in alchemyresults['sentiment'].keys():
                    sentiment_score = alchemyresults['sentiment']['docSentiment']['score'] if 'score' in alchemyresults['sentiment']['docSentiment'].keys() else 0
                    sentiment_type  = alchemyresults['sentiment']['docSentiment']['type'] if 'type' in alchemyresults['sentiment']['docSentiment'].keys() else ''

            if alchemyresults['entities']['status'] == 'OK':
                if 'entities' in alchemyresults['entities'].keys():
                    for entity in alchemyresults['entities']['entities']:
                        entities.append({
                            'text'      :   entity['text'] if 'text' in entity.keys() else '',
                            'relevance' :   entity['relevance'] if 'relevance' in entity.keys() else '',
                            'count'     :   entity['count'] if 'count' in entity.keys() else '',
                            'type'      :   [entity['type']] if 'type' in entity.keys() else [''],
                            'sentiment' :   entity['sentiment'] if 'sentiment' in entity.keys() else ''
                        })
                        # add in disambiguated data
                        if 'disambiguated' in entity.keys():
                            entity_type = entities[-1]['type']
                            if 'type' in entity['disambiguated'].keys():
                                entity_type.append(entity['disambiguated']['type'])
                            if 'subType' in entity['disambiguated'].keys():
                                entity_type += entity['disambiguated']['subType']
                            entities[-1]['type'] = entity_type

            #print sentiment_score, sentiment_type, '\n', entities

            metrics_base = {
                        'name'          : '_'.join(self.filters) + '/overall/sentiment',
                        'timestamp'     : time_queried,
                        'value'         : sentiment_score
                    }
            metrics_entity = {}

            if entities:
                for entity in entities:
                    for what in ['sentiment', 'count', 'relevance']:
                        what_name = what if what != 'sentiment' else 'entity_sentiment'
                        value = entity[what] if 'score' not in entity[what] else entity[what]['score']
                        print 'What_name: ', what_name, ' value: ', value, ' from: ', entity[what], '\n'
                        metrics_entity = {
                            'name'          : '_'.join(self.filters) + '/' + entity['text'].lower().replace(' ', '_') + '/' + what_name,
                            'timestamp'     : time_queried,
                            'value'         : value if value and type(value) is not dict else 0
                        }
                        for eachtype in entity['type']:
                            tags = {'type': eachtype }
                            metrics.append(
                                dict(metrics_entity, **{'tags': tags})    
                            )
                        if 'type' in entity[what]:
                            tags = {'textSentiment': entity[what]['type'] }
                            metrics.append(
                                dict(metrics_entity, **{'tags': tags})    
                            )
            
            for filter in self.filters:
                tags = {'filter':filter}
                tags['textSentiment'] = sentiment_type if sentiment_type else 'not_applicable'
                metrics.append(
                    dict(metrics_base, **{'tags': tags})
                )

            print "\nWILL SEND THIS: ", simplejson.dumps(metrics, sort_keys=True, indent=3)

            print '\n===================='

            for individual_metric in metrics:
                status = pushToKairos(individual_metric)
                if status.status_code != 204:
                    raise Exception('KairosDB Issue...', status.text)                

        return True
        #except BaseException, e:
        #    print "Failed ondata, ", str(e)
        #    time.sleep(5) # in case of rate limiting

    def on_error(self, status_code):
        print 'An error has occured! Status code = %s' % status_code
        return True  # keep stream alive

    def on_timeout(self):
        print 'Snoozing Zzzzzz'

def pushToKairos(metrics):
    """
    Let's push into KairosDB

    Data will come in as such:

    metrics: {
        'name'          : 'filterList:<overall|entityName>:<entity|count>',
        'time_queried'  : <timestamp>,
        'value'         : <somevalue>,
        'tags'          : {
                'filter|user1'  : <filter|user1>,
                ...
                'filter|userN'  : <filter|userN>,
                'entity1'       : <entity1>,
                ...
                'entityN'       : <entityN>,
                ...
                'textSentiment' : <positive|negative|neutral>
        }
    }

    """
    import json, requests

    ### YOU NEED TO CHANGE THIS TO YOUR KAIROS INSTALLATION ENDPOINT ###
    PORT = 8080
    BASE_URL    =   'http://localhost:' + str(PORT) + '/api/v1/datapoints'

    return requests.post(url=BASE_URL, data=json.dumps(metrics))

def main():
    consumer_key = ckey
    consumer_secret = csecret
    access_token = atoken
    access_token_secret = asecret

    # Prompt for login credentials and setup stream object
    consumer_key = raw_input('Consumer Key: ') if not consumer_key else consumer_key
    consumer_secret = getpass('Consumer Secret: ') if not consumer_secret else consumer_secret
    access_token = raw_input('Access Token: ') if not access_token else access_token
    access_token_secret = getpass('Access Token Secret: ') if not access_token_secret else access_token_secret

    auth = tweepy.auth.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    swl = StreamWatcherListener()
    stream = tweepy.Stream(auth, swl, timeout=None)

    # Prompt for mode of streaming
    valid_modes = ['sample', 'filter']
    while True:
        mode = raw_input('Mode? [sample/filter] ')
        if mode in valid_modes:
            break
        print 'Invalid mode! Try again.'

    if mode == 'sample':
        stream.sample()

    elif mode == 'filter':
        follow_list = raw_input('Users to follow (comma separated): ').strip()
        track_list = raw_input('Keywords to track (comma seperated): ').strip()
        if follow_list:
            follow_list = [u for u in follow_list.split(',')]
            userid_list = []
            username_list = []
            
            for user in follow_list:
                if user.isdigit():
                    userid_list.append(user)
                else:
                    username_list.append(user)
            
            for username in username_list:
                user = tweepy.API().get_user(username)
                userid_list.append(user.id)
            
            follow_list = userid_list            
        else:
            follow_list = None
        if track_list:
            track_list = [k for k in track_list.split(',')]
        else:
            track_list = None
        
        # keep these around for later...
        swl.users   = follow_list
        swl.filters = track_list

        stream.filter(follow_list, track_list)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print '\nGoodbye!'
